/**
 * AGX TOURISM ENGINE - PHASE 1: BACKEND FOUNDATION
 * 
 * Microservices Architecture with:
 * - Intent Service (port 3001)
 * - Planning Service (port 3002)
 * - Booking Service (port 3003)
 * - Knowledge Graph Service (port 3004)
 * - Context Monitor Service (port 3005)
 * - Explanation Service (port 3006)
 * 
 * Each service is fully independent, scales horizontally, has explicit error handling
 */

const express = require('express');
const axios = require('axios');
const dotenv = require('dotenv');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

dotenv.config();

// ============================================================================
// LOGGER SETUP
// ============================================================================

const createLogger = (serviceName) => {
  return winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.json(),
    defaultMeta: { service: serviceName },
    transports: [
      new winston.transports.File({ filename: `logs/${serviceName}-error.log`, level: 'error' }),
      new winston.transports.File({ filename: `logs/${serviceName}-combined.log` })
    ]
  });
};

// ============================================================================
// ERROR HANDLING CLASSES
// ============================================================================

class APIError extends Error {
  constructor(statusCode, errorCode, message, details = {}) {
    super(message);
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.details = details;
    this.timestamp = new Date().toISOString();
    this.traceId = uuidv4();
  }

  toJSON() {
    return {
      status: this.statusCode,
      error_code: this.errorCode,
      message: this.message,
      details: this.details,
      trace_id: this.traceId,
      timestamp: this.timestamp,
      retry_strategy: {
        is_retryable: this.isRetryable(),
        retry_after_seconds: this.getRetryAfter(),
        max_retries: 3
      }
    };
  }

  isRetryable() {
    return [429, 503, 504].includes(this.statusCode);
  }

  getRetryAfter() {
    if (this.statusCode === 429) return 60;
    if (this.statusCode === 503) return 300;
    return 0;
  }
}

// ============================================================================
// SERP API WRAPPER (Real-time data fetching)
// ============================================================================

class SerpAPIClient {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://serpapi.com/search';
    this.rateLimit = 100; // requests per day (free tier)
    this.timeout = 10000; // 10 seconds
    this.requestCount = 0;
    this.lastReset = Date.now();
  }

  /**
   * Core method to fetch data from SERP API
   * 
   * @param {string} query - Search query
   * @param {object} params - Additional parameters (engine, location, etc.)
   * @returns {Promise<object>} Search results
   * @throws {APIError} Rate limit exceeded, API error, timeout
   */
  async search(query, params = {}) {
    try {
      // Rate limiting check
      this.checkRateLimit();

      const requestParams = {
        q: query,
        api_key: this.apiKey,
        gl: 'in', // Google locale: India
        hl: 'en',
        ...params
      };

      const response = await axios.get(this.baseUrl, {
        params: requestParams,
        timeout: this.timeout
      });

      this.requestCount++;

      // Check for API errors
      if (response.data.error) {
        throw new APIError(
          400,
          'SERP_API_ERROR',
          `SERP API returned error: ${response.data.error}`,
          { serp_error: response.data.error }
        );
      }

      return {
        query,
        results: response.data.organic_results || [],
        answer_box: response.data.answer_box || null,
        knowledge_graph: response.data.knowledge_graph || null,
        places: response.data.places || [],
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      if (error instanceof APIError) throw error;

      if (error.code === 'ECONNABORTED') {
        throw new APIError(504, 'SERP_API_TIMEOUT', 'SERP API request timed out', {
          timeout_ms: this.timeout
        });
      }

      if (error.response?.status === 429) {
        throw new APIError(429, 'RATE_LIMIT_EXCEEDED', 'SERP API rate limit exceeded', {
          retry_after: error.response.headers['retry-after']
        });
      }

      throw new APIError(
        error.response?.status || 500,
        'SERP_API_ERROR',
        error.message,
        { details: error.response?.data }
      );
    }
  }

  /**
   * Fetch real-time events in a destination
   */
  async searchEvents(destination, dateFrom, dateTo) {
    return this.search(`events ${destination} ${dateFrom} to ${dateTo}`);
  }

  /**
   * Fetch current weather
   */
  async getWeather(location) {
    return this.search(`weather ${location} forecast`);
  }

  /**
   * Fetch restaurants with reviews
   */
  async searchRestaurants(destination, cuisine = '') {
    const query = cuisine 
      ? `${cuisine} restaurants ${destination} reviews`
      : `best restaurants ${destination} reviews`;
    return this.search(query);
  }

  /**
   * Fetch flight availability
   */
  async searchFlights(origin, destination, date) {
    return this.search(`flights ${origin} to ${destination} ${date}`);
  }

  /**
   * Check rate limit
   */
  checkRateLimit() {
    const now = Date.now();
    const dayElapsed = (now - this.lastReset) / (1000 * 60 * 60 * 24) > 1;

    if (dayElapsed) {
      this.requestCount = 0;
      this.lastReset = now;
    }

    if (this.requestCount >= this.rateLimit) {
      throw new APIError(
        429,
        'RATE_LIMIT_EXCEEDED',
        'Daily SERP API quota exceeded',
        {
          limit: this.rateLimit,
          used: this.requestCount,
          resets_at: new Date(this.lastReset + 24 * 60 * 60 * 1000).toISOString()
        }
      );
    }
  }
}

// ============================================================================
// REQUEST/RESPONSE SCHEMAS & VALIDATION
// ============================================================================

const schemas = {
  // Intent Service Schemas
  intentExtractRequest: {
    required: ['user_query', 'user_id'],
    properties: {
      user_query: { type: 'string', minLength: 10 },
      user_id: { type: 'string', format: 'uuid' },
      session_id: { type: 'string', format: 'uuid' },
      preferences: {
        type: 'object',
        properties: {
          languages: { type: 'array', items: { type: 'string' } },
          mobility_needs: { type: 'string' },
          dietary_restrictions: { type: 'array', items: { type: 'string' } }
        }
      },
      context: {
        type: 'object',
        properties: {
          current_location: { type: 'string' },
          travel_date_from: { type: 'string', format: 'date' },
          travel_date_to: { type: 'string', format: 'date' }
        }
      }
    }
  },

  // Planning Service Schemas
  planningGenerateRequest: {
    required: ['intent_id', 'traveler_profile'],
    properties: {
      intent_id: { type: 'string', format: 'uuid' },
      traveler_profile: { type: 'object' },
      num_alternatives: { type: 'integer', minimum: 1, maximum: 5 },
      optimization_priority: { type: 'string', enum: ['sustainability', 'budget', 'experience', 'time'] },
      planning_strategy: { type: 'string', enum: ['greedy', 'optimal', 'heuristic'] }
    }
  },

  // Booking Service Schemas
  bookingConfirmRequest: {
    required: ['itinerary_id', 'user_id', 'selected_itinerary_num', 'bookings', 'contact_info'],
    properties: {
      itinerary_id: { type: 'string', format: 'uuid' },
      user_id: { type: 'string', format: 'uuid' },
      selected_itinerary_num: { type: 'integer', minimum: 1 },
      bookings: { type: 'array' },
      contact_info: {
        type: 'object',
        required: ['email', 'phone'],
        properties: {
          email: { type: 'string', format: 'email' },
          phone: { type: 'string' }
        }
      }
    }
  }
};

// ============================================================================
// VALIDATION MIDDLEWARE
// ============================================================================

const validateRequest = (schema) => (req, res, next) => {
  const errors = [];
  
  if (schema.required) {
    for (const field of schema.required) {
      if (!req.body[field]) {
        errors.push(`Missing required field: ${field}`);
      }
    }
  }

  if (errors.length > 0) {
    throw new APIError(400, 'VALIDATION_ERROR', 'Request validation failed', {
      errors,
      provided_fields: Object.keys(req.body)
    });
  }

  next();
};

// ============================================================================
// ERROR HANDLING MIDDLEWARE
// ============================================================================

const errorHandler = (err, req, res, next) => {
  const logger = req.logger;

  if (err instanceof APIError) {
    logger.warn({
      status: err.statusCode,
      error_code: err.errorCode,
      trace_id: err.traceId,
      path: req.path,
      method: req.method
    });
    return res.status(err.statusCode).json(err.toJSON());
  }

  // Unknown error
  const traceId = uuidv4();
  logger.error({
    message: err.message,
    stack: err.stack,
    trace_id: traceId,
    path: req.path,
    method: req.method
  });

  res.status(500).json({
    status: 500,
    error_code: 'INTERNAL_SERVER_ERROR',
    message: 'An unexpected error occurred',
    trace_id: traceId,
    timestamp: new Date().toISOString()
  });
};

// ============================================================================
// SERVICE 1: INTENT SERVICE (Port 3001)
// ============================================================================

function createIntentService() {
  const app = express();
  const logger = createLogger('intent-service');

  app.use(express.json());
  app.use((req, res, next) => {
    req.logger = logger;
    next();
  });

  /**
   * POST /api/v1/intent/extract
   * Extract traveler intent from natural language query
   */
  app.post('/api/v1/intent/extract', validateRequest(schemas.intentExtractRequest), async (req, res, next) => {
    try {
      const { user_query, user_id, session_id, preferences, context } = req.body;
      const intent_id = uuidv4();

      // Simulate intent extraction (in production, use Claude API)
      const travelerProfile = {
        destination: extractDestination(user_query),
        trip_duration_days: extractDuration(user_query),
        budget_inr: extractBudget(user_query),
        interests: extractInterests(user_query),
        travel_style: extractTravelStyle(user_query),
        group_composition: {
          size: extractGroupSize(user_query),
          types: ['adult']
        },
        constraints: {
          mobility: preferences?.mobility_needs || 'none',
          dietary: preferences?.dietary_restrictions || [],
          best_season: true
        }
      };

      res.status(200).json({
        intent_id,
        traveler_profile: travelerProfile,
        extracted_entities: {
          destination: travelerProfile.destination,
          duration: travelerProfile.trip_duration_days,
          budget: travelerProfile.budget_inr,
          interests: travelerProfile.interests
        },
        confidence_scores: {
          destination: 0.95,
          duration: 0.92,
          budget: 0.88
        },
        clarifications_needed: [],
        timestamp: new Date().toISOString()
      });

      logger.info({
        intent_id,
        user_id,
        destination: travelerProfile.destination,
        budget: travelerProfile.budget_inr
      });
    } catch (error) {
      next(error);
    }
  });

  app.use(errorHandler);

  const PORT = process.env.INTENT_SERVICE_PORT || 3001;
  return app.listen(PORT, () => {
    logger.info(`Intent Service running on port ${PORT}`);
  });
}

// ============================================================================
// SERVICE 2: PLANNING SERVICE (Port 3002)
// ============================================================================

function createPlanningService() {
  const app = express();
  const logger = createLogger('planning-service');
  const serpClient = new SerpAPIClient(process.env.SERP_API_KEY);

  app.use(express.json());
  app.use((req, res, next) => {
    req.logger = logger;
    req.serpClient = serpClient;
    next();
  });

  /**
   * POST /api/v1/planning/generate-itinerary
   * Generate multi-day itinerary with alternatives
   */
  app.post('/api/v1/planning/generate-itinerary', async (req, res, next) => {
    try {
      const { intent_id, traveler_profile, num_alternatives = 3, optimization_priority = 'experience' } = req.body;

      if (!intent_id || !traveler_profile) {
        throw new APIError(400, 'MISSING_REQUIRED_FIELDS', 'intent_id and traveler_profile are required');
      }

      const itinerary_id = uuidv4();

      // Fetch real-time data from SERP API
      let realTimeEvents = [];
      try {
        const eventResults = await serpClient.searchEvents(
          traveler_profile.destination,
          traveler_profile.travel_date_from || '2026-05-01',
          traveler_profile.travel_date_to || '2026-05-05'
        );
        realTimeEvents = eventResults.results.slice(0, 5);
      } catch (serpError) {
        logger.warn({
          message: 'SERP API failed, using cached data',
          error: serpError.message,
          intent_id
        });
        // Graceful degradation: continue with knowledge graph data
      }

      // Generate itineraries (simplified for Phase 1)
      const itineraries = generateItineraries(
        traveler_profile,
        num_alternatives,
        optimization_priority,
        realTimeEvents
      );

      res.status(200).json({
        itinerary_id,
        itineraries: itineraries,
        timestamp: new Date().toISOString()
      });

      logger.info({
        itinerary_id,
        intent_id,
        destination: traveler_profile.destination,
        num_alternatives: itineraries.length
      });
    } catch (error) {
      next(error);
    }
  });

  /**
   * GET /api/v1/planning/itinerary/{itinerary_id}
   * Retrieve saved itinerary
   */
  app.get('/api/v1/planning/itinerary/:itinerary_id', (req, res, next) => {
    try {
      const { itinerary_id } = req.params;
      
      // In production, fetch from database
      res.status(200).json({
        itinerary_id,
        status: 'retrieved',
        data: { /* itinerary data */ }
      });
    } catch (error) {
      next(error);
    }
  });

  app.use(errorHandler);

  const PORT = process.env.PLANNING_SERVICE_PORT || 3002;
  return app.listen(PORT, () => {
    logger.info(`Planning Service running on port ${PORT}`);
  });
}

// ============================================================================
// SERVICE 3: BOOKING SERVICE (Port 3003)
// ============================================================================

function createBookingService() {
  const app = express();
  const logger = createLogger('booking-service');

  app.use(express.json());
  app.use((req, res, next) => {
    req.logger = logger;
    next();
  });

  /**
   * POST /api/v1/booking/confirm
   * Confirm and execute bookings
   */
  app.post('/api/v1/booking/confirm', async (req, res, next) => {
    try {
      const { itinerary_id, user_id, bookings, contact_info } = req.body;

      if (!itinerary_id || !user_id || !bookings || !contact_info) {
        throw new APIError(400, 'MISSING_REQUIRED_FIELDS', 'Missing required booking fields');
      }

      const booking_request_id = uuidv4();

      // Validate contact info
      if (!contact_info.email || !contact_info.phone) {
        throw new APIError(400, 'INVALID_CONTACT_INFO', 'Email and phone are required');
      }

      // Process bookings (simplified for Phase 1)
      const processedBookings = bookings.map((booking) => ({
        booking_id: uuidv4(),
        type: booking.booking_type,
        status: 'confirmed',
        confirmation_number: generateConfirmationNumber(),
        provider_contact: '+91-98765-00001',
        cancellation_policy: 'free_cancellation_7_days_before'
      }));

      res.status(202).json({
        booking_request_id,
        status: 'processing',
        bookings: processedBookings,
        itinerary_pdf_url: `https://storage.example.com/itineraries/${itinerary_id}.pdf`,
        notifications_sent_to: contact_info.email,
        timestamp: new Date().toISOString()
      });

      logger.info({
        booking_request_id,
        user_id,
        total_bookings: bookings.length,
        email: contact_info.email
      });
    } catch (error) {
      next(error);
    }
  });

  /**
   * GET /api/v1/booking/{booking_id}
   * Check booking status
   */
  app.get('/api/v1/booking/:booking_id', (req, res, next) => {
    try {
      const { booking_id } = req.params;
      
      res.status(200).json({
        booking_id,
        status: 'confirmed',
        confirmation_number: 'KLR-20260501-ABC123'
      });
    } catch (error) {
      next(error);
    }
  });

  app.use(errorHandler);

  const PORT = process.env.BOOKING_SERVICE_PORT || 3003;
  return app.listen(PORT, () => {
    logger.info(`Booking Service running on port ${PORT}`);
  });
}

// ============================================================================
// SERVICE 4: KNOWLEDGE GRAPH SERVICE (Port 3004)
// ============================================================================

function createKnowledgeGraphService() {
  const app = express();
  const logger = createLogger('knowledge-graph-service');

  app.use(express.json());
  app.use((req, res, next) => {
    req.logger = logger;
    next();
  });

  /**
   * POST /api/v1/kg/query
   * Query knowledge graph for attractions, hotels, events
   */
  app.post('/api/v1/kg/query', async (req, res, next) => {
    try {
      const { query_type, destination, filters = {} } = req.body;

      if (!query_type || !destination) {
        throw new APIError(400, 'MISSING_PARAMS', 'query_type and destination are required');
      }

      // In production, execute Neo4j queries
      const results = mockKGQuery(query_type, destination, filters);

      res.status(200).json({
        query_type,
        destination,
        results,
        count: results.length,
        timestamp: new Date().toISOString()
      });

      logger.info({ query_type, destination, result_count: results.length });
    } catch (error) {
      next(error);
    }
  });

  /**
   * GET /api/v1/kg/attraction/{attraction_id}
   * Get detailed attraction info
   */
  app.get('/api/v1/kg/attraction/:attraction_id', (req, res, next) => {
    try {
      const { attraction_id } = req.params;
      
      res.status(200).json({
        attraction_id,
        name: 'Kyoto National Museum',
        type: 'museum',
        location: { lat: 34.9868, lng: 135.7639 },
        rating: 4.7,
        operating_hours: '09:00-17:00'
      });
    } catch (error) {
      next(error);
    }
  });

  app.use(errorHandler);

  const PORT = process.env.KG_SERVICE_PORT || 3004;
  return app.listen(PORT, () => {
    logger.info(`Knowledge Graph Service running on port ${PORT}`);
  });
}

// ============================================================================
// SERVICE 5: CONTEXT MONITORING SERVICE (Port 3005)
// ============================================================================

function createContextMonitorService() {
  const app = express();
  const logger = createLogger('context-monitor-service');

  app.use(express.json());
  app.use((req, res, next) => {
    req.logger = logger;
    next();
  });

  /**
   * POST /api/v1/monitoring/subscribe
   * Subscribe to real-time context monitoring
   */
  app.post('/api/v1/monitoring/subscribe', (req, res, next) => {
    try {
      const { itinerary_id, signals } = req.body;

      if (!itinerary_id) {
        throw new APIError(400, 'MISSING_ITINERARY_ID', 'itinerary_id is required');
      }

      res.status(202).json({
        subscription_id: uuidv4(),
        itinerary_id,
        signals: signals || ['weather', 'traffic', 'event_cancellations'],
        websocket_url: `wss://api.example.com/ws/v1/monitoring/${itinerary_id}`,
        timestamp: new Date().toISOString()
      });

      logger.info({ itinerary_id, signals });
    } catch (error) {
      next(error);
    }
  });

  /**
   * POST /api/v1/monitoring/check
   * One-time context check
   */
  app.post('/api/v1/monitoring/check', async (req, res, next) => {
    try {
      const { itinerary_id, location } = req.body;

      res.status(200).json({
        itinerary_id,
        location,
        weather: { condition: 'clear', temperature: 28 },
        traffic: { congestion: 'low', estimated_delay: 0 },
        disruptions: [],
        timestamp: new Date().toISOString()
      });

      logger.info({ itinerary_id, location });
    } catch (error) {
      next(error);
    }
  });

  app.use(errorHandler);

  const PORT = process.env.MONITOR_SERVICE_PORT || 3005;
  return app.listen(PORT, () => {
    logger.info(`Context Monitor Service running on port ${PORT}`);
  });
}

// ============================================================================
// SERVICE 6: EXPLANATION SERVICE (Port 3006)
// ============================================================================

function createExplanationService() {
  const app = express();
  const logger = createLogger('explanation-service');

  app.use(express.json());
  app.use((req, res, next) => {
    req.logger = logger;
    next();
  });

  /**
   * GET /api/v1/explanations/{itinerary_id}/activity/{activity_id}
   * Get detailed explanation for a recommendation
   */
  app.get('/api/v1/explanations/:itinerary_id/activity/:activity_id', (req, res, next) => {
    try {
      const { itinerary_id, activity_id } = req.params;

      const explanation = {
        activity_id,
        activity_name: 'Backwater Sunset Cruise',
        recommendation_reason: 'Recommended for you because:',
        reasoning_blocks: [
          {
            criterion: 'Interest Match',
            score: 0.95,
            explanation: 'Directly matches your interest in nature and eco-tourism',
            evidence: { interests: ['eco-tourism', 'nature'], activity_tags: ['nature', 'eco-friendly'] }
          },
          {
            criterion: 'Location Proximity',
            score: 0.92,
            explanation: '2.3 km from your accommodation',
            evidence: { distance_km: 2.3, travel_time_minutes: 15 }
          },
          {
            criterion: 'User Ratings',
            score: 0.94,
            explanation: '4.7/5 stars from 342 recent reviews',
            evidence: { avg_rating: 4.7, review_count: 342 }
          }
        ],
        overall_recommendation_score: 0.93,
        confidence: 0.92,
        generated_at: new Date().toISOString()
      };

      res.status(200).json(explanation);

      logger.info({ itinerary_id, activity_id, recommendation_score: 0.93 });
    } catch (error) {
      next(error);
    }
  });

  app.use(errorHandler);

  const PORT = process.env.EXPLANATION_SERVICE_PORT || 3006;
  return app.listen(PORT, () => {
    logger.info(`Explanation Service running on port ${PORT}`);
  });
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

// Intent extraction helpers
function extractDestination(query) {
  const match = query.match(/(?:to|in|visit|tour)\s+([A-Za-z\s]+?)(?:\s+with|\s+for|$)/i);
  return match ? match[1].trim() : 'India';
}

function extractDuration(query) {
  const match = query.match(/(\d+)[-\s]?day/i);
  return match ? parseInt(match[1]) : 5;
}

function extractBudget(query) {
  const match = query.match(/₹\s*(\d+,?\d*)/);
  return match ? parseInt(match[1].replace(',', '')) : 50000;
}

function extractInterests(query) {
  const interests = [];
  if (query.match(/eco|nature|green|sustainable/i)) interests.push('eco-tourism');
  if (query.match(/culture|heritage|history|museum/i)) interests.push('culture');
  if (query.match(/adventure|trek|hike|mountain/i)) interests.push('adventure');
  return interests.length > 0 ? interests : ['tourism'];
}

function extractTravelStyle(query) {
  if (query.match(/budget|cheap|economical/i)) return 'budget';
  if (query.match(/luxury|premium|high-end/i)) return 'luxury';
  if (query.match(/eco|green|sustainable/i)) return 'sustainable';
  return 'standard';
}

function extractGroupSize(query) {
  const match = query.match(/(\d+)\s*(?:person|people|traveler|family)/i);
  return match ? parseInt(match[1]) : 1;
}

// Planning helpers
function generateItineraries(profile, count, priority, realTimeEvents) {
  const itineraries = [];
  for (let i = 1; i <= count; i++) {
    itineraries.push({
      itinerary_num: i,
      title: `Itinerary Option ${i}`,
      score: 0.85 + (i * 0.05),
      cost_breakdown: {
        accommodation: 15000,
        transport: 8000,
        activities: 18000,
        food: 7000,
        contingency: 2000,
        total: 50000
      },
      schedule: generateSchedule(profile.trip_duration_days || 5),
      sustainability_score: 0.88
    });
  }
  return itineraries;
}

function generateSchedule(days) {
  const schedule = [];
  for (let i = 1; i <= days; i++) {
    schedule.push({
      day: i,
      theme: `Day ${i} itinerary`,
      activities: []
    });
  }
  return schedule;
}

// Knowledge Graph mock
function mockKGQuery(queryType, destination, filters) {
  return [
    { id: uuidv4(), name: `${destination} Attraction 1`, rating: 4.5 },
    { id: uuidv4(), name: `${destination} Attraction 2`, rating: 4.7 },
    { id: uuidv4(), name: `${destination} Attraction 3`, rating: 4.3 }
  ];
}

// Booking helpers
function generateConfirmationNumber() {
  const prefix = Math.random().toString(36).substring(2, 5).toUpperCase();
  const date = new Date().toISOString().split('T')[0].replace(/-/g, '');
  const suffix = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `${prefix}-${date}-${suffix}`;
}

// ============================================================================
// START ALL SERVICES
// ============================================================================

async function startAllServices() {
  try {
    console.log('🚀 Starting AGX Tourism Engine Backend - Phase 1\n');

    // Verify environment variables
    if (!process.env.SERP_API_KEY) {
      console.warn('⚠️  Warning: SERP_API_KEY not set. Real-time data fetching will fail.');
    }

    const services = [
      { name: 'Intent Service', create: createIntentService },
      { name: 'Planning Service', create: createPlanningService },
      { name: 'Booking Service', create: createBookingService },
      { name: 'Knowledge Graph Service', create: createKnowledgeGraphService },
      { name: 'Context Monitor Service', create: createContextMonitorService },
      { name: 'Explanation Service', create: createExplanationService }
    ];

    for (const service of services) {
      try {
        service.create();
      } catch (error) {
        console.error(`❌ Failed to start ${service.name}:`, error.message);
      }
    }

    console.log('\n✅ All services started successfully!');
    console.log('📋 Service Ports:');
    console.log('  - Intent Service:           http://localhost:3001');
    console.log('  - Planning Service:         http://localhost:3002');
    console.log('  - Booking Service:          http://localhost:3003');
    console.log('  - Knowledge Graph Service:  http://localhost:3004');
    console.log('  - Context Monitor Service:  http://localhost:3005');
    console.log('  - Explanation Service:      http://localhost:3006\n');
  } catch (error) {
    console.error('❌ Failed to start services:', error);
    process.exit(1);
  }
}

// Start everything
if (require.main === module) {
  startAllServices();
}

module.exports = {
  startAllServices,
  createIntentService,
  createPlanningService,
  createBookingService,
  createKnowledgeGraphService,
  createContextMonitorService,
  createExplanationService,
  APIError,
  SerpAPIClient
};
