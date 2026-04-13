function validateJson(req, res, next) {
  if (!req.is('application/json')) {
    return res.status(415).json({ message: 'Content-Type must be application/json' });
  }
  return next();
}

module.exports = { validateJson };
