# IKEA Stock API

A Python web application for tracking and displaying IKEA product stock levels across Hong Kong and Macau stores.

## Features

- Real-time stock checking for IKEA products
- Web interface for easy access to stock information
- Product information stored in CSV format
- Automatic product image management
- 4-hour cache for stock data to reduce API load

## Project Structure

```
.
├── web_app.py                    # Flask web application
├── stock_checker.py              # Stock checking functionality
├── config.py                     # Configuration settings
├── ikea_products.csv            # Product database
├── ikea_products_with_images.csv # Product database with image information
├── templates/                   # HTML templates
│   └── index.html              # Main web interface
├── static/                     # Static assets
│   └── product_images/        # Product images
└── requirements.txt            # Project dependencies
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up your Firecrawl API key in `config.py`

## Usage

Start the web application:
```bash
python web_app.py
```

The web interface will be available at `http://localhost:5000`

## Stock Information

Stock levels are tracked for the following locations:
- Warehouse
- Causeway Bay
- Kowloon Bay
- Macau Taipa
- Shatin
- Tsuen Wan

## Features

### Stock Caching
- Stock data is cached for 4 hours to reduce API load
- Cache is automatically refreshed when expired

### Price Formatting
- Prices are displayed in HKD with proper formatting
- Handles various price formats including those with commas

### Image Management
- Product images are stored locally
- Automatic symbolic link creation for serving images through Flask

## Technical Details

- Built with Flask web framework
- Uses Firecrawl API for stock checking
- CSV-based product database for simplicity and portability
- Implements error handling and rate limiting
- Asynchronous stock checking capabilities

## Error Handling

The application includes:
- Graceful handling of API failures
- Cache management for reliability
- Proper error messages for various scenarios
- Fallback mechanisms for missing data
