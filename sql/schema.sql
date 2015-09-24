-- MySQL dump 10.13  Distrib 5.5.44, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: dynip
-- ------------------------------------------------------
-- Server version	5.5.44-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `allocated_blocks`
--

DROP TABLE IF EXISTS `allocated_blocks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `allocated_blocks` (
  `allocation_id` int(11) NOT NULL AUTO_INCREMENT,
  `allocated_block` varchar(37) NOT NULL,
  `network_id` int(11) NOT NULL,
  `machine_id` int(11) NOT NULL,
  `status` ENUM('UNMANAGED', 'RESERVED', 'STANDBY', 'ACTIVE_UTILIZATION') NOT NULL,
  `reservation_expires` datetime NOT NULL,
  PRIMARY KEY (`allocation_id`),
  UNIQUE KEY `allocation_id` (`allocation_id`),
  KEY `network_id` (`network_id`),
  KEY `network_id_idx_fkey` (`network_id`),
  KEY `machine_id` (`machine_id`),
  CONSTRAINT `machine_id_fkey` FOREIGN KEY (`machine_id`) REFERENCES `machine_info` (`id`),
  CONSTRAINT `network_id_fkey` FOREIGN KEY (`network_id`) REFERENCES `network_topology` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ip_allocations`
--

DROP TABLE IF EXISTS `ip_allocations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ip_allocations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_allocation` int(11) NOT NULL,
  `allocated_to` int(11) NOT NULL,
  `ip_address` varchar(37) NOT NULL,
  `status` enum('UNMANAGED','RESERVED','STANDBY','ACTIVE_UTILIZATION') NOT NULL,
  PRIMARY KEY (`id`),
  KEY `allocation_id` (`from_allocation`),
  KEY `allocated_to` (`allocated_to`),
  CONSTRAINT `allocated_to_fkey` FOREIGN KEY (`allocated_to`) REFERENCES `machine_info` (`id`),
  CONSTRAINT `from_allocation_fkey` FOREIGN KEY (`from_allocation`) REFERENCES `allocated_blocks` (`allocation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `machine_info`
--

DROP TABLE IF EXISTS `machine_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `machine_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `token` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `network_topology`
--

DROP TABLE IF EXISTS `network_topology`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `network_topology` (
  `id` int(11) AUTO_INCREMENT DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  `family` tinyint(4) NOT NULL,
  `network` varchar(37) NOT NULL,
  `allocation_size` int(11) NOT NULL,
  `reserved_blocks` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
