// CloudFront Function for Request Routing
// Routes requests to the optimal region based on geographic location

function handler(event) {
    var request = event.request;
    var headers = request.headers;
    var clientIP = request.clientIp;
    
    // Get the CloudFront-Viewer-Country header
    var country = headers['cloudfront-viewer-country'] ? 
        headers['cloudfront-viewer-country'].value : 'US';
    
    // Get the CloudFront-Viewer-Country-Region header
    var region = headers['cloudfront-viewer-country-region'] ? 
        headers['cloudfront-viewer-country-region'].value : 'US-VA';
    
    // Determine optimal origin based on geographic location
    var optimalOrigin = getOptimalOrigin(country, region);
    
    // Set the origin based on the optimal region
    request.origin = {
        custom: {
            domainName: getOriginDomain(optimalOrigin),
            port: 443,
            protocol: 'https',
            path: '',
            sslProtocols: ['TLSv1.2'],
            readTimeout: 30,
            keepaliveTimeout: 5,
            customHeaders: {
                'X-Region': { value: optimalOrigin },
                'X-Client-Country': { value: country },
                'X-Client-Region': { value: region }
            }
        }
    };
    
    // Add custom headers for analytics
    request.headers['X-CloudFront-Region'] = { value: optimalOrigin };
    request.headers['X-CloudFront-Country'] = { value: country };
    
    return request;
}

function getOptimalOrigin(country, region) {
    // Geographic routing logic
    var countryCode = country.toUpperCase();
    var regionCode = region.toUpperCase();
    
    // North America
    if (['US', 'CA', 'MX'].includes(countryCode)) {
        return 'us-east-1';
    }
    
    // Europe
    if (['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'PL', 'CZ', 'HU', 'RO', 'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'LU', 'MT', 'CY', 'GR'].includes(countryCode)) {
        return 'eu-west-1';
    }
    
    // Asia Pacific
    if (['JP', 'KR', 'CN', 'IN', 'SG', 'MY', 'TH', 'ID', 'PH', 'VN', 'TW', 'HK', 'AU', 'NZ'].includes(countryCode)) {
        return 'ap-southeast-1';
    }
    
    // Default to US East for other regions
    return 'us-east-1';
}

function getOriginDomain(region) {
    var domainMap = {
        'us-east-1': 'riches-reach-prod-us-east-1-alb-1234567890.us-east-1.elb.amazonaws.com',
        'eu-west-1': 'riches-reach-prod-eu-west-1-alb-1234567890.eu-west-1.elb.amazonaws.com',
        'ap-southeast-1': 'riches-reach-prod-ap-southeast-1-alb-1234567890.ap-southeast-1.elb.amazonaws.com'
    };
    
    return domainMap[region] || domainMap['us-east-1'];
}
