DROP TABLE IF EXIST network_topology;
CREATE TABLE `network_topology` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `location` varchar(255) NOT NULL,
  `protocol` tinyint(4) NOT NULL,
  `network` varchar(255) NOT NULL,
  `allocation_size` int(11) NOT NULL,
  `reserved_blocks` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;
