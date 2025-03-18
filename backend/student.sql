/*
 Navicat Premium Dump SQL

 Source Server         : MySQL
 Source Server Type    : MySQL
 Source Server Version : 80404 (8.4.4)
 Source Host           : 192.168.10.115:3306
 Source Schema         : student

 Target Server Type    : MySQL
 Target Server Version : 80404 (8.4.4)
 File Encoding         : 65001

 Date: 18/03/2025 18:01:52
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for announce
-- ----------------------------
DROP TABLE IF EXISTS `announce`;
CREATE TABLE `announce`  (
  `id` int NOT NULL,
  `text` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for deduction_records
-- ----------------------------
DROP TABLE IF EXISTS `deduction_records`;
CREATE TABLE `deduction_records`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `points` int NOT NULL,
  `reason` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `operator` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `student_id`(`student_id` ASC) USING BTREE,
  INDEX `idx_deduction_created`(`created_at` ASC) USING BTREE,
  CONSTRAINT `deduction_records_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `deduction_records_chk_1` CHECK (`points` > 0)
) ENGINE = InnoDB AUTO_INCREMENT = 102 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for students
-- ----------------------------
DROP TABLE IF EXISTS `students`;
CREATE TABLE `students`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `class_number` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT '2',
  `gender` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `student_number` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `student_number`(`student_number` ASC) USING BTREE,
  INDEX `idx_student_class`(`class_number` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 49 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Procedure structure for GetDeductionStats
-- ----------------------------
DROP PROCEDURE IF EXISTS `GetDeductionStats`;
delimiter ;;
CREATE PROCEDURE `GetDeductionStats`()
BEGIN
    -- 总扣分TOP10
    SELECT s.name, SUM(dr.points) AS total_points
    FROM deduction_records dr
    JOIN students s ON dr.student_id = s.id
    WHERE s.class_number = '2'
    GROUP BY s.id
    ORDER BY total_points DESC
    LIMIT 10;

    -- 最近30天趋势
    SELECT
        DATE(dr.created_at) AS date,
        COUNT(*) AS count,
        SUM(dr.points) AS points
    FROM deduction_records dr
    JOIN students s ON dr.student_id = s.id
    WHERE s.class_number = '2'
        AND dr.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY DATE(dr.created_at);
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
