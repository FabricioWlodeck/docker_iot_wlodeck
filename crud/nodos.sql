USE sensores_remotos;

CREATE TABLE IF NOT EXISTS nodos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sensor_id VARCHAR(50) UNIQUE NOT NULL,
  nombre VARCHAR(100),
  topico VARCHAR(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO nodos (sensor_id, nombre, topico) VALUES
('nodo_destinatario_1', 'Nodo Destinatario 1', 'iot/nodo_destinatario_1/comandos'),
('nodo_destinatario_2', 'Nodo Destinatario 2', 'iot/nodo_destinatario_2/comandos'),
('nodo_destinatario_3', 'Nodo Destinatario 3', 'iot/nodo_destinatario_3/comandos');

GRANT SELECT, INSERT, UPDATE, DELETE ON sensores_remotos.nodos TO 'crud'@'%';
