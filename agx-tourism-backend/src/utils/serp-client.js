const axios = require('axios');

class SerpAPIClient {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://serpapi.com/search';
  }

  async search(query, params = {}) {
    const response = await axios.get(this.baseUrl, {
      params: { q: query, api_key: this.apiKey, ...params },
      timeout: 10000
    });
    return response.data;
  }
}

module.exports = { SerpAPIClient };
