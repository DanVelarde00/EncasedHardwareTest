#ifndef CONFIG_H
#define CONFIG_H

// =============================================================================
// STEP Configuration - Hardware Pin Definitions and Constants
// =============================================================================

// -----------------------------------------------------------------------------
// Pin Definitions
// -----------------------------------------------------------------------------
#define PIN_SDA         18      // I2C Data
#define PIN_SCL         19      // I2C Clock
#define PIN_BUZZER      4       // Piezo buzzer
#define PIN_LED_DATA    5       // WS2812B data line
#define PIN_SD_CS       BUILTIN_SDCARD  // Teensy 4.1 built-in SD

// -----------------------------------------------------------------------------
// I2C Addresses
// -----------------------------------------------------------------------------
#define H3LIS331DL_ADDR 0x19    // High-g accelerometer (SA0 high)
#define MPU6050_ADDR    0x68    // Gyro/accel IMU (AD0 low)
#define SSD1306_ADDR    0x3C    // OLED display (optional future)

// -----------------------------------------------------------------------------
// Sensor Configuration
// -----------------------------------------------------------------------------
#define H3LIS_RANGE     H3LIS331DL_RANGE_400_G  // ±400g range
#define H3LIS_DATARATE  LIS331_DATARATE_1000_HZ // 1000 Hz ODR
#define MPU_ACCEL_RANGE MPU6050_RANGE_16_G      // ±16g range
#define MPU_GYRO_RANGE  MPU6050_RANGE_2000_DEG  // ±2000 °/s

// -----------------------------------------------------------------------------
// Logging Configuration
// -----------------------------------------------------------------------------
#define SAMPLE_RATE_HZ      1000    // Target sample rate
#define SAMPLE_INTERVAL_US  1000    // Microseconds between samples (1000 Hz)
#define PRE_TRIGGER_MS      100     // Buffer before trigger
#define POST_TRIGGER_MS     2000    // Continue logging after impact
#define TRIGGER_THRESHOLD_G 5.0     // G-force to trigger logging

// -----------------------------------------------------------------------------
// LED Configuration
// -----------------------------------------------------------------------------
#define NUM_LEDS        5       // Number of WS2812B LEDs
#define LED_BRIGHTNESS  64      // 0-255, keep low for battery life

// -----------------------------------------------------------------------------
// Self-Test Thresholds
// -----------------------------------------------------------------------------
#define BATTERY_MIN_V       3.5     // Minimum battery voltage
#define ACCEL_REST_TOL_G    0.15    // Tolerance for 1g at rest (±0.15g)
#define GYRO_REST_TOL_DPS   5.0     // Tolerance for 0°/s at rest

// -----------------------------------------------------------------------------
// Timing
// -----------------------------------------------------------------------------
#define BOOT_DELAY_MS       1000    // Delay on boot for power stabilization
#define I2C_CLOCK_HZ        400000  // 400 kHz I2C clock
#define SERIAL_BAUD         115200  // Serial monitor baud rate

// -----------------------------------------------------------------------------
// File Naming
// -----------------------------------------------------------------------------
#define LOG_FILE_PREFIX     "STEP_"
#define LOG_FILE_EXT        ".csv"
#define SELFTEST_FILE       "selftest_log.txt"

// -----------------------------------------------------------------------------
// Status Codes
// -----------------------------------------------------------------------------
enum SystemState {
    STATE_BOOT,
    STATE_SELFTEST,
    STATE_IDLE,
    STATE_ARMED,
    STATE_TRIGGERED,
    STATE_LOGGING,
    STATE_COMPLETE,
    STATE_ERROR
};

// -----------------------------------------------------------------------------
// Self-Test Result Bits
// -----------------------------------------------------------------------------
#define TEST_POWER      0x01    // Bit 0: Power system
#define TEST_I2C        0x02    // Bit 1: I2C bus scan
#define TEST_HIGHG      0x04    // Bit 2: H3LIS331DL calibration
#define TEST_GYRO       0x08    // Bit 3: MPU6050 gyro zero
#define TEST_SD         0x10    // Bit 4: SD card read/write
#define TEST_OLED       0x20    // Bit 5: OLED display (optional)
#define TEST_LED        0x40    // Bit 6: LED strip
#define TEST_BUZZER     0x80    // Bit 7: Buzzer

#endif // CONFIG_H
