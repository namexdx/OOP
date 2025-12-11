import os
import json
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify, g
import psycopg2
from psycopg2 import extras
import redis
from kafka import KafkaProducer
from kafka.errors import KafkaError

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'database': os.getenv('DB_NAME', 'bookdb'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASS', 'password')
}

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'redis'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'decode_responses': True
}

KAFKA_CONFIG = {
    'bootstrap_servers': [os.getenv('KAFKA_BROKER_HOST', 'kafka:9092')],
    'topic': os.getenv('KAFKA_TOPIC', 'car_events'),
    'dead_letter_topic': os.getenv('DEAD_LETTER_TOPIC', 'dead_letter_events')
}


import os
from logging.handlers import RotatingFileHandler

os.makedirs('logs', exist_ok=True)

file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=2 * 1024 * 1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        file_handler
    ]
)
logger = logging.getLogger(__name__)

redis_client = None
kafka_producer = None
dead_letter_producer = None

def get_db_connection():
    """Get database connection with retry logic"""
    if 'db_conn' not in g or g.db_conn.closed:
        max_retries = 10
        for attempt in range(max_retries):
            try:
                g.db_conn = psycopg2.connect(**DB_CONFIG)
                logger.info("✅ Database connection established")
                return g.db_conn
            except Exception as e:
                logger.warning(f"⚠️ Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)
    return g.db_conn

@app.teardown_appcontext
def close_db_connection(exception):
    """Close database connection after request"""
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()

def init_kafka_producer():
    """Initialize Kafka producer with error handling"""
    global kafka_producer, dead_letter_producer
    
    max_retries = 15
    for attempt in range(max_retries):
        try:
            kafka_producer = KafkaProducer(
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                acks='all',
                retries=3,
                request_timeout_ms=10000,
                api_version=(2, 0, 2)
            )
            
            dead_letter_producer = KafkaProducer(
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
            )
            
            # Test connection
            # kafka_producer.list_topics()
            logger.info("✅ Kafka producers initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Kafka producer attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                logger.error("❌ Failed to initialize Kafka producers")
                return False
            time.sleep(3)

def init_redis():
    """Initialize Redis connection"""
    global redis_client
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            redis_client = redis.Redis(**REDIS_CONFIG)
            redis_client.ping()
            logger.info("✅ Redis connection established")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                logger.error("❌ Failed to connect to Redis")
                redis_client = None
                return False
            time.sleep(2)

def init_database():
    """Initialize database tables and sample data"""
    max_retries = 10
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cars (
                        id SERIAL PRIMARY KEY,
                        make VARCHAR(255) NOT NULL,
                        model VARCHAR(255) NOT NULL,
                        year INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute("SELECT COUNT(*) FROM cars")
                if cursor.fetchone()[0] == 0:
                    sample_cars = [
                        ('Toyota', 'Camry', 2020),
                        ('Honda', 'Civic', 2019),
                        ('Ford', 'Mustang', 2021)
                    ]
                    cursor.executemany(
                        "INSERT INTO cars (make, model, year) VALUES (%s, %s, %s)",
                        sample_cars
                    )
                    logger.info(f"✅ Inserted {len(sample_cars)} sample cars")
                
                conn.commit()
            conn.close()
            logger.info("✅ Database initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Database initialization attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                logger.error("❌ Failed to initialize database")
                return False
            time.sleep(2)

def publish_kafka_event(action, car_data=None, car_id=None):
    """Publish event to Kafka topic with error handling"""
    if not kafka_producer:
        logger.error("❌ Kafka producer not available")
        return False
    
    try:
        event = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_ip': request.remote_addr,
            'car_id': car_id,
            'data': car_data
        }
        
        future = kafka_producer.send(KAFKA_CONFIG['topic'], value=event)
        # Wait for message to be delivered
        future.get(timeout=10)
        
        logger.info(f"✅ Event published: {action} for car {car_id}")
        return True
        
    except KafkaError as e:
        logger.error(f"❌ Kafka error: {e}")
        send_to_dead_letter_queue(event, str(e))
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error publishing event: {e}")
        return False

def send_to_dead_letter_queue(event, error_message):
    """Send failed messages to dead letter queue"""
    if dead_letter_producer:
        try:
            dead_event = {
                **event,
                'error': error_message,
                'dead_letter_timestamp': datetime.now().isoformat()
            }
            dead_letter_producer.send(KAFKA_CONFIG['dead_letter_topic'], value=dead_event)
            logger.info("✅ Message sent to dead letter queue")
        except Exception as e:
            logger.error(f"❌ Failed to send to dead letter queue: {e}")

request_stats = {
    'total_requests': 0,
    'average_time': 0,
    'endpoints': {}
}

def update_statistics(endpoint, execution_time):
    """Update request statistics"""
    request_stats['total_requests'] += 1
    
    total_time = request_stats['average_time'] * (request_stats['total_requests'] - 1) + execution_time
    request_stats['average_time'] = total_time / request_stats['total_requests']
    
    if endpoint not in request_stats['endpoints']:
        request_stats['endpoints'][endpoint] = {
            'count': 0,
            'total_time': 0,
            'average_time': 0,
            'min_time': float('inf'),
            'max_time': 0
        }
    
    stats = request_stats['endpoints'][endpoint]
    stats['count'] += 1
    stats['total_time'] += execution_time
    stats['average_time'] = stats['total_time'] / stats['count']
    stats['min_time'] = min(stats['min_time'], execution_time)
    stats['max_time'] = max(stats['max_time'], execution_time)

@app.before_request
def before_request():
    """Log incoming requests"""
    g.start_time = time.time()
    logger.info(f"📥 Incoming: {request.method} {request.path}")

@app.after_request
def after_request(response):
    """Log outgoing responses and update statistics"""
    execution_time = time.time() - g.start_time
    endpoint = f"{request.method} {request.path}"
    
    update_statistics(endpoint, execution_time)
    
    logger.info(f"📤 Outgoing: {response.status_code} for {endpoint} - {execution_time:.3f}s")
    return response


@app.route('/')
def index():
    """API information"""
    return jsonify({
        'message': 'Car Inventory API with Kafka',
        'endpoints': {
            'GET /cars': 'Get all cars',
            'GET /cars/{id}': 'Get car by ID',
            'POST /cars': 'Create new car',
            'PUT /cars/{id}': 'Update car',
            'DELETE /cars/{id}': 'Delete car',
            'GET /stats': 'Get request statistics',
            'GET /health': 'Health check'
        }
    })

@app.route('/cars', methods=['GET'])
def get_cars():
    """Get all cars with Redis caching"""
    cache_key = 'all_cars'
    
    if redis_client:
        try:
            cached_cars = redis_client.get(cache_key)
            if cached_cars:
                logger.info("🚗 Cars retrieved from cache")
                return jsonify(json.loads(cached_cars))
        except Exception as e:
            logger.warning(f"⚠️ Redis cache error: {e}")
    
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            cursor.execute("SELECT id, make, model, year FROM cars ORDER BY id")
            cars = cursor.fetchall()
        
        if redis_client:
            try:
                redis_client.setex(
                    cache_key,
                    int(os.getenv('REDIS_CACHE_TIMEOUT', 30)),
                    json.dumps([dict(car) for car in cars], ensure_ascii=False)
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache in Redis: {e}")
        
        logger.info(f"🚗 Retrieved {len(cars)} cars from database")
        return jsonify([dict(car) for car in cars])
        
    except Exception as e:
        logger.error(f"❌ Error getting cars: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/cars/<int:car_id>', methods=['GET'])
def get_car(car_id):
    """Get car by ID"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, make, model, year FROM cars WHERE id = %s",
                (car_id,)
            )
            car = cursor.fetchone()
        
        if car:
            logger.info(f"🚘 Retrieved car ID {car_id}")
            return jsonify(dict(car))
        else:
            logger.warning(f"❌ Car {car_id} not found")
            return jsonify({'error': 'Car not found'}), 404
            
    except Exception as e:
        logger.error(f"❌ Error getting car {car_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/cars', methods=['POST'])
def create_car():
    """Create new car"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        required_fields = ['make', 'model', 'year']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': f'Missing required fields: {required_fields}'
            }), 400
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            cursor.execute('''
                INSERT INTO cars (make, model, year)
                VALUES (%s, %s, %s)
                RETURNING id, make, model, year
            ''', (data['make'], data['model'], data['year']))
            
            new_car = cursor.fetchone()
            conn.commit()
        
        if redis_client:
            redis_client.delete('all_cars')
        
        publish_kafka_event('car_created', dict(new_car), new_car['id'])
        
        logger.info(f"✅ Created car: {new_car['make']} {new_car['model']} (ID: {new_car['id']})")
        return jsonify(dict(new_car)), 201
        
    except Exception as e:
        logger.error(f"❌ Error creating car: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/cars/<int:car_id>', methods=['PUT'])
def update_car(car_id):
    """Update car"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            update_fields = []
            values = []
            
            for field in ['make', 'model', 'year']:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    values.append(data[field])
            
            if not update_fields:
                return jsonify({'error': 'No fields to update'}), 400
            
            values.append(car_id)
            query = f"""
                UPDATE cars
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, make, model, year
            """
            
            cursor.execute(query, values)
            updated_car = cursor.fetchone()
            
            if not updated_car:
                return jsonify({'error': 'Car not found'}), 404
            
            conn.commit()
        
        if redis_client:
            redis_client.delete('all_cars')
        
        publish_kafka_event('car_updated', dict(updated_car), car_id)
        
        logger.info(f"✅ Updated car ID {car_id}")
        return jsonify(dict(updated_car))
        
    except Exception as e:
        logger.error(f"❌ Error updating car {car_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/cars/<int:car_id>', methods=['DELETE'])
def delete_car(car_id):
    """Delete car"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT make, model FROM cars WHERE id = %s", (car_id,))
            car_info = cursor.fetchone()
            
            if not car_info:
                return jsonify({'error': 'Car not found'}), 404
            
            cursor.execute("DELETE FROM cars WHERE id = %s", (car_id,))
            conn.commit()
        
        if redis_client:
            redis_client.delete('all_cars')
        
        publish_kafka_event('car_deleted', {
            'make': car_info[0],
            'model': car_info[1]
        }, car_id)
        
        logger.info(f"✅ Deleted car ID {car_id}")
        return jsonify({'message': f'Car {car_id} deleted successfully'})
        
    except Exception as e:
        logger.error(f"❌ Error deleting car {car_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get request statistics"""
    return jsonify(request_stats)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {}
    }
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['services']['database'] = 'healthy'
    except Exception as e:
        status['services']['database'] = f'unhealthy: {e}'
        status['status'] = 'degraded'
    
    if redis_client:
        try:
            redis_client.ping()
            status['services']['redis'] = 'healthy'
        except Exception as e:
            status['services']['redis'] = f'unhealthy: {e}'
            status['status'] = 'degraded'
    else:
        status['services']['redis'] = 'not connected'
    
    if kafka_producer:
        try:
            test_future = kafka_producer.send(KAFKA_CONFIG['topic'], value={'test': 'health_check'})
            status['services']['kafka'] = 'healthy'
        except Exception as e:
            status['services']['kafka'] = f'unhealthy: {e}'
            status['status'] = 'degraded'
    else:
        status['services']['kafka'] = 'not connected'
    
    return jsonify(status)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def initialize_services():
    """Initialize all services"""
    logger.info("🚀 Initializing services...")
    
    init_database()
    init_redis()
    init_kafka_producer()
    
    logger.info("✅ All services initialized successfully")

if __name__ == '__main__':
    initialize_services()
    
    logger.info("""
    🚗 Car Inventory API with Kafka
    ==============================
    Available endpoints:
    GET    /              - API information
    GET    /cars         - Get all cars
    GET    /cars/{id}    - Get car by ID
    POST   /cars         - Create new car
    PUT    /cars/{id}    - Update car
    DELETE /cars/{id}    - Delete car
    GET    /stats         - Request statistics
    GET    /health        - Health check
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=False)