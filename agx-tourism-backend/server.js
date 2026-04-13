/**
 * Entry point for AGX backend.
 * This keeps compatibility with the current monolithic phase-1 implementation.
 */

const { startAllServices } = require('./agx-backend-phase1');

startAllServices();
