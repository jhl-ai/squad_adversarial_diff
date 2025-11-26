def enable_ssl_bypass():
    """
    Applies aggressive SSL bypassing for requests, urllib, and aiohttp (used by datasets 3.0+).
    Call this function at the very start of your script.
    """
    # AIOHTTP Patch (CRITICAL FOR DATASETS 3.0+)
    # Datasets 3.0+ uses aiohttp for async downloads. We must patch the connector.
    try:
        import aiohttp
        
        # Store the original __init__
        original_connector_init = aiohttp.TCPConnector.__init__
        
        # Define a patched __init__ that forces ssl=False
        def patched_connector_init(self, *args, **kwargs):
            # Forcefully disable SSL verification for any aiohttp connection
            kwargs['ssl'] = False
            original_connector_init(self, *args, **kwargs)
            
        # Apply the monkey patch
        aiohttp.TCPConnector.__init__ = patched_connector_init
        print("DEBUG: Applied aiohttp SSL patch for Datasets 3.0+")
    except ImportError:
        pass # aiohttp might not be installed in older envs