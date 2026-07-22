-- ==========================================================
-- شمای پایگاه داده ربات مدیریت فروشگاه تلگرام
-- ==========================================================

PRAGMA foreign_keys = ON;

-- جدول کاربران
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id   INTEGER NOT NULL UNIQUE,
    username      TEXT,
    full_name     TEXT NOT NULL,
    phone_number  TEXT,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    is_blocked    INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- جدول دسته‌بندی‌ها
CREATE TABLE IF NOT EXISTS categories (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    description   TEXT,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- جدول محصولات
CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id   INTEGER NOT NULL,
    name          TEXT NOT NULL,
    description   TEXT,
    price         INTEGER NOT NULL CHECK (price >= 0),
    stock         INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT
);

-- جدول تصاویر محصولات (هر محصول می‌تواند چند تصویر داشته باشد)
CREATE TABLE IF NOT EXISTS product_images (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    INTEGER NOT NULL,
    file_id       TEXT NOT NULL,
    sort_order    INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

-- جدول سبد خرید (هر ردیف یک قلم از سبد خرید یک کاربر است)
CREATE TABLE IF NOT EXISTS cart_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    product_id    INTEGER NOT NULL,
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    UNIQUE (user_id, product_id)
);

-- جدول سفارش‌ها
CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    total_price    INTEGER NOT NULL DEFAULT 0,
    status         TEXT NOT NULL DEFAULT 'pending',
    address        TEXT,
    phone_number   TEXT,
    admin_note     TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT
);

-- جدول اقلام سفارش
CREATE TABLE IF NOT EXISTS order_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      INTEGER NOT NULL,
    product_id    INTEGER NOT NULL,
    product_name  TEXT NOT NULL,
    unit_price    INTEGER NOT NULL,
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
);

-- جدول لاگ فعالیت‌ها
CREATE TABLE IF NOT EXISTS activity_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER,
    action        TEXT NOT NULL,
    details       TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- ایندکس‌ها برای بهبود کارایی جستجو
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category_id);
CREATE INDEX IF NOT EXISTS idx_products_name ON products (name);
CREATE INDEX IF NOT EXISTS idx_products_active ON products (is_active);
CREATE INDEX IF NOT EXISTS idx_cart_user ON cart_items (user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders (user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_logs_user ON activity_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_logs_created ON activity_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id);
