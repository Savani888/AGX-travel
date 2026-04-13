const winston = require('winston');

function createLogger(serviceName) {
  return winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.json(),
    defaultMeta: { service: serviceName },
    transports: [
      new winston.transports.File({ filename: `logs/${serviceName}-error.log`, level: 'error' }),
      new winston.transports.File({ filename: `logs/${serviceName}-combined.log` })
    ]
  });
}

module.exports = { createLogger };
