-- ==========================================================
-- شمای پایگاه داده ربات مدیریت فروشگاه تلگرام (نسخه PostgreSQL)
-- ==========================================================

-- جدول کاربران
CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    telegram_id   BIGINT NOT NULL UNIQUE,
    username      TEXT,
    full_name     TEXT NOT NULL,
    phone_number  TEXT,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    is_blocked    INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
    updated_at    TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')
);

-- جدول دسته‌بندی‌ها
CREATE TABLE IF NOT EXISTS categories (
    id            BIGSERIAL PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    description   TEXT,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')
);

-- جدول محصولات
CREATE TABLE IF NOT EXISTS products (
    id            BIGSERIAL PRIMARY KEY,
    category_id   BIGINT NOT NULL,
    name          TEXT NOT NULL,
    description   TEXT,
    price         BIGINT NOT NULL CHECK (price >= 0),
    stock         INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
    updated_at    TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT
);

-- جدول تصاویر محصولات (هر محصول می‌تواند چند تصویر داشته باشد)
CREATE TABLE IF NOT EXISTS product_images (
    id            BIGSERIAL PRIMARY KEY,
    product_id    BIGINT NOT NULL,
    file_id       TEXT NOT NULL,
    sort_order    INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

-- جدول سبد خرید (هر ردیف یک قلم از سبد خرید یک کاربر است)
CREATE TABLE IF NOT EXISTS cart_items (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    product_id    BIGINT NOT NULL,
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    created_at    TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    UNIQUE (user_id, product_id)
);

-- جدول سفارش‌ها
CREATE TABLE IF NOT EXISTS orders (
    id             BIGSERIAL PRIMARY KEY,
    user_id        BIGINT NOT NULL,
    total_price    BIGINT NOT NULL DEFAULT 0,
    status         TEXT NOT NULL DEFAULT 'pending',
    address        TEXT,
    phone_number   TEXT,
    admin_note     TEXT,
    created_at     TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
    updated_at     TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT
);

-- جدول اقلام سفارش
CREATE TABLE IF NOT EXISTS order_items (
    id            BIGSERIAL PRIMARY KEY,
    order_id      BIGINT NOT NULL,
    product_id    BIGINT NOT NULL,
    product_name  TEXT NOT NULL,
    unit_price    BIGINT NOT NULL,
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
);

-- جدول لاگ فعالیت‌ها
CREATE TABLE IF NOT EXISTS activity_logs (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT,
    action        TEXT NOT NULL,
    details       TEXT,
    created_at    TEXT NOT NULL DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
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
