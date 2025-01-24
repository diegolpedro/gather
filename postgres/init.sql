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

-- DROP TABLE IF EXISTS securities_data;
CREATE TABLE securities_data (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    symbol TEXT,                         -- Símbolo único para cada registro
    settlement TEXT,                     -- Plazo de loquidacion 
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
    panel TEXT                           -- Panel
);

-------------------------------------------------------------------------------
-- COTIZACION ACTUAL TABLE
-------------------------------------------------------------------------------
-- DROP TABLE IF EXISTS cotizacion_actual;
CREATE TABLE cotizacion_actual(
    -- titulo_id           int PRIMARY KEY,
    symbol TEXT,                         -- Símbolo único para cada registro
    settlement TEXT,                     -- Plazo de loquidacion 
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
    panel TEXT,                           -- Panel
    PRIMARY KEY(symbol, settlement)
    -- FOREIGN KEY(titulo_id) REFERENCES titulo_t(titulo_id)
);


-------------------------------------------------------------------------------
-- COTIZACION DIARIA TABLE
-------------------------------------------------------------------------------
-- DROP TABLE cotizacion_diaria;
CREATE TABLE cotizacion_diaria(
    symbol TEXT,                         -- Símbolo único para cada registro
    settlement TEXT,                     -- Plazo de loquidacion 
    last NUMERIC,                        -- Último precio
    change NUMERIC,                      -- Cambio porcentual
    open NUMERIC,                        -- Precio de apertura
    high NUMERIC,                        -- Precio máximo
    low NUMERIC,                         -- Precio mínimo
    previous_close NUMERIC,              -- Precio de cierre anterior
    turnover BIGINT,                     -- Volumen de negocios
    volume BIGINT,                       -- Volumen total
    operations INTEGER,                  -- Número de operaciones
    date DATE,                           -- Fecha y hora del registro
    expiration DATE,                     -- Fecha de vencimiento
    strike NUMERIC,                      -- Precio de ejercicio
    kind TEXT,                           -- Tipo de opción (CALL/PUT)
    underlying_asset TEXT,               -- Activo subyacente
    UNIQUE (symbol, settlement, date)
    -- FOREIGN KEY(titulo_id) REFERENCES titulo_t(titulo_id)
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

--- Options 

DROP TRIGGER IF EXISTS update_cot_actual_trigger ON options_data;
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
CREATE TRIGGER update_cot_actual_trigger AFTER INSERT
    ON options_data
    FOR EACH ROW
    EXECUTE PROCEDURE update_cot_actual_function();

--- Securities

DROP TRIGGER IF EXISTS update_securities_actual_trigger ON securities_data;
DROP FUNCTION IF EXISTS update_securities_actual();

CREATE FUNCTION update_securities_actual()
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
                                settlement = NEW.settlement,
                                panel = NEW.panel
       WHERE symbol = NEW.symbol AND settlement = NEW.settlement;
       RETURN NULL;
    END;
    $$;
CREATE TRIGGER update_securities_actual_trigger AFTER INSERT
    ON securities_data
    FOR EACH ROW
    EXECUTE PROCEDURE update_securities_actual();
