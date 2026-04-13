class APIError extends Error {
  constructor(statusCode, errorCode, message, details = {}) {
    super(message);
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.details = details;
    this.timestamp = new Date().toISOString();
  }
}

module.exports = { APIError };
