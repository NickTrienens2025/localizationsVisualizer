# Contentful Localization Service

A modern Python web service for managing and viewing Contentful localization files with a beautiful web interface.

## Features

- 🌐 **Modern Web Interface**: Beautiful, responsive UI built with Bootstrap 5
- 📊 **Real-time Data**: Live data from Contentful with automatic refresh
- 🔍 **Search & Sort**: Advanced search and sorting capabilities
- 📁 **Section Organization**: Browse content by sections and subsections
- 🌍 **Multi-language Support**: View English and French translations side-by-side
- 📱 **Mobile Friendly**: Responsive design that works on all devices
- 🔄 **Auto-refresh**: Automatic data refresh every 5 minutes
- 📋 **Copy to Clipboard**: Easy copying of IDs and keys
- 🚀 **Fast API**: JSON endpoints for integration with other services
- 🐳 **Docker Ready**: Containerized for easy deployment

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)
- Contentful account with API tokens

### Environment Setup

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` with your Contentful credentials:
   ```bash
   SPACE_ID=your_space_id_here
   ENVIRONMENT_ID=master
   TOKEN=your_content_delivery_api_token_here
   GRAPH_TOKEN=your_graphql_api_token_here
   HOST=0.0.0.0
   PORT=8888
   ```

### Running with Docker

1. Build the Docker image:
   ```bash
   docker build -t contentful-localization .
   ```

2. Run the container:
   ```bash
   docker run -p 8888:8888 --env-file .env contentful-localization
   ```

### Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open your browser and navigate to `http://localhost:8888`

## API Endpoints

### Web Interface
- `GET /` - Dashboard
- `GET /table` - Table view of all localization entries
- `GET /sections` - Table view of sections
- `GET /sections/view` - Sections overview
- `GET /section/{id}/view` - Individual section detail view

### JSON API
- `GET /api/entries` - Get all entries
- `GET /api/sections` - Get all sections
- `GET /api/section/{id}` - Get specific section
- `GET /api/localization` - Get all localization files
- `GET /api/manifest` - Get manifest of available JSON files
- `GET /health` - Health check endpoint

## Project Structure

```
ContentfulServicePy/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── env.example           # Environment variables template
├── README.md             # This file
├── services/             # Business logic services
│   ├── contentful_service.py  # Contentful API integration
│   └── graph_service.py       # GraphQL queries
├── controllers/          # Request handlers
│   ├── table_controller.py    # Table view logic
│   ├── section_controller.py  # Section view logic
│   └── json_controller.py     # JSON API logic
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── dashboard.html    # Dashboard page
    ├── table.html        # Entries table
    ├── sections_overview.html  # Sections overview
    ├── section_detail.html     # Section detail
    ├── sections_table.html     # Sections table
    └── error.html        # Error page
```

## Contentful Content Types

This service expects the following Contentful content types:

**Note:** The actual Contentful model names can be configured in `app.py` via the `CONTENTFUL_MODELS` configuration dictionary. By default, they map to `localizationEntry` and `localizedSection` respectively.

### Localization Entry (`localizationEntry`)
- `key` (Symbol) - The localization key
- `value` (Text, localized) - The translation value
- `lineNumber` (Symbol) - Line number reference
- `originalKey` (Symbol) - Original key reference
- `section` (Symbol) - Section name
- `androidOriginalKey` (Symbol) - Android-specific key

### Localized Section (`localizedSection`)
- `title` (Symbol) - Section title
- `key` (Symbol) - Section key
- `values` (Array, Link to Localization Entry) - Section values
- `subsections` (Array, Link to Localized Section) - Subsections

## Features in Detail

### Dashboard
- Overview cards with quick access to different views
- Statistics and information about the service
- API documentation

### Table Views
- Searchable and sortable tables
- Modal popups for detailed information
- Copy-to-clipboard functionality
- Auto-refresh every 5 minutes

### Section Views
- Hierarchical organization of content
- Card-based layout for easy browsing
- Detailed section views with subsections
- Value counts and statistics

### API Integration
- RESTful JSON endpoints
- Comprehensive error handling
- Caching for improved performance
- Health check endpoint

## Development

### Adding New Features

1. **New Service**: Add business logic in the `services/` directory
2. **New Controller**: Add request handling in the `controllers/` directory
3. **New Template**: Add HTML templates in the `templates/` directory
4. **New Route**: Add routes in `app.py`

### Testing

The service includes comprehensive error handling and logging. For production deployment, consider adding:

- Unit tests with pytest
- Integration tests
- Load testing
- Monitoring and alerting

### Deployment

The service is designed to be deployed in containers. For production:

1. Use a proper reverse proxy (nginx)
2. Set up SSL/TLS certificates
3. Configure proper logging
4. Set up monitoring and alerting
5. Use environment-specific configurations

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check your Contentful API tokens and space ID
2. **Missing Content**: Ensure your Contentful space has the expected content types
3. **Port Conflicts**: Change the PORT environment variable if 8888 is in use

### Logs

The service logs to stdout/stderr. In Docker, view logs with:
```bash
docker logs <container_name>
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Open an issue on GitHub 