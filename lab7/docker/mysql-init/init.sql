CREATE DATABASE IF NOT EXISTS spacecream
CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;

USE spacecream;

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    image_path VARCHAR(255),
    description TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    priority INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO users (username, email, password, priority) VALUES
('root', 'root@gmail.com', 'root', 2);

INSERT INTO products (name, price, image_path, description) VALUES
('Pistachio Ice Cream', 180.00, 'uploads/1733673100581.png', 'Nutty pistachio ice cream'),
('Blueberry Ice Cream', 160.00, 'uploads/1733673663251.png', 'Fresh blueberry ice cream'),
('Chocolate-Vanilla Ice Cream', 185.00, 'uploads/1733676213857.png', 'Chocolate and vanilla combo'),
('Hazelnut Ice Cream', 190.00, 'uploads/1733676226079.png', 'Ice cream with hazelnuts'),
('Coconut Ice Cream', 165.00, 'uploads/1733676250572.png', 'Creamy coconut ice cream'),
('Raspberry Ice Cream', 170.00, 'uploads/1733676266770.png', 'Sweet raspberry ice cream'),
('Chocolate-Hazelnut Ice Cream', 200.00, 'uploads/1733676280901.png', 'Chocolate ice cream with hazelnuts'),
('Banana-Caramel Ice Cream', 185.00, 'uploads/1733676297891.png', 'Banana with caramel ice cream'),
('Mixed Berries Ice Cream', 180.00, 'uploads/1733676320987.png', 'A mix of forest berries');

