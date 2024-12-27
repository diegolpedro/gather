-------------------------------------------------------------------------------
-- AIRFLOW
-------------------------------------------------------------------------------
    CREATE USER airflow_user WITH PASSWORD 'airflow_pass';
    CREATE DATABASE airflow_db WITH OWNER airflow_user;
    GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;
    GRANT ALL ON SCHEMA public TO airflow_user;


-------------------------------------------------------------------------------
-- COTIZACION OPCIONES TABLE
-------------------------------------------------------------------------------
CREATE TABLE options_data (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    symbol TEXT,                         -- Símbolo único para cada registro
    bid_size INTEGER,                    -- Tamaño de la oferta
    bid NUMERIC,                         -- Precio de la oferta
    ask NUMERIC,                         -- Precio de la demanda
    ask_size INTEGER,                    -- Tamaño de la demanda
    last NUMERIC,                        -- Último precio
    change NUMERIC,                      -- Cambio porcentual
    open NUMERIC,                        -- Precio de apertura
    high NUMERIC,                        -- Precio máximo
    low NUMERIC,                         -- Precio mínimo
    previous_close NUMERIC,              -- Precio de cierre anterior
    turnover BIGINT,                     -- Volumen de negocios
    volume BIGINT,                       -- Volumen total
    operations INTEGER,                  -- Número de operaciones
    datetime TIMESTAMP,                  -- Fecha y hora del registro
    expiration DATE,                     -- Fecha de vencimiento
    strike NUMERIC,                      -- Precio de ejercicio
    kind TEXT,                           -- Tipo de opción (CALL/PUT)
    underlying_asset TEXT                -- Activo subyacente
);


-------------------------------------------------------------------------------
-- COTIZACION ACTUAL TABLE
-------------------------------------------------------------------------------
CREATE TABLE cotizacion_actual(
    symbol TEXT PRIMARY KEY,             -- Símbolo único para cada registro
    last NUMERIC,                        -- Último precio
    change NUMERIC,                      -- Cambio porcentual
    open NUMERIC,                        -- Precio de apertura
    high NUMERIC,                        -- Precio máximo
    low NUMERIC,                         -- Precio mínimo
    previous_close NUMERIC,              -- Precio de cierre anterior
    turnover BIGINT,                     -- Volumen de negocios
    volume BIGINT,                       -- Volumen total
    operations INTEGER,                  -- Número de operaciones
    datetime TIMESTAMP,                  -- Fecha y hora del registro
    expiration DATE,                     -- Fecha de vencimiento
    strike NUMERIC,                      -- Precio de ejercicio
    kind TEXT,                           -- Tipo de opción (CALL/PUT)
    underlying_asset TEXT                -- Activo subyacente
);


-------------------------------------------------------------------------------
-- COTIZACION DIARIA TABLE
-------------------------------------------------------------------------------
-- DROP TABLE cotizacion_diaria;
CREATE TABLE cotizacion_diaria(
    symbol TEXT,                         -- Símbolo único para cada registro
    last NUMERIC,                        -- Último precio
    change NUMERIC,                      -- Cambio porcentual
    open NUMERIC,                        -- Precio de apertura
    high NUMERIC,                        -- Precio máximo
    low NUMERIC,                         -- Precio mínimo
    previous_close NUMERIC,              -- Precio de cierre anterior
    turnover BIGINT,                     -- Volumen de negocios
    volume BIGINT,                       -- Volumen total
    operations INTEGER,                  -- Número de operaciones
    datetime TIMESTAMP,                  -- Fecha y hora del registro
    expiration DATE,                     -- Fecha de vencimiento
    strike NUMERIC,                      -- Precio de ejercicio
    kind TEXT,                           -- Tipo de opción (CALL/PUT)
    underlying_asset TEXT,               -- Activo subyacente
    PRIMARY KEY (symbol, datetime)
);


-------------------------------------------------------------------------------
-- PARAMETROS
-------------------------------------------------------------------------------
-- DROP TABLE parametro;
CREATE TABLE parametro(
    parametro_id    SERIAL,
    nombre          varchar(10),
    valor           varchar(256),
    PRIMARY KEY(parametro_id)
);

-- Horarios
INSERT INTO parametro(nombre, valor)
VALUES ('H_INI', '11:00'), ('H_FIN', '17:00');


-------------------------------------------------------------------------------
-- TRIGGERS
-------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS update_cot_actual_function();
CREATE FUNCTION update_cot_actual_function()
   RETURNS TRIGGER 
   LANGUAGE PLPGSQL
    AS $$
    BEGIN
       UPDATE cotizacion_actual SET last = NEW.last, 
                                change = NEW.change,
                                open = NEW.open,
                                high = NEW.high,
                                low = NEW.low,
                                previous_close = NEW.previous_close,
                                turnover = NEW.turnover,
                                volume = NEW.volume,
                                operations = NEW.operations,
                                datetime = NEW.datetime,
                                expiration = NEW.expiration,
                                strike = NEW.strike,
                                kind= NEW.kind,
                                underlying_asset = NEW.underlying_asset
       WHERE symbol = NEW.symbol;
       RETURN NULL;
    END;
    $$;

DROP TRIGGER IF EXISTS update_cot_actual_trigger
ON options_data;
CREATE TRIGGER update_cot_actual_trigger AFTER INSERT
    ON options_data
    FOR EACH ROW
    EXECUTE PROCEDURE update_cot_actual_function();


-- INSERT INTO cotizacion_actual (symbol)
-- SELECT DISTINCT symbol
-- FROM options_data
-- WHERE symbol not in ( 
--     SELECT DISTINCT symbol
--     FROM cotizacion_actual);
