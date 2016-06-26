API_CALL_DELAY = 0.36
API_BASE_URL = "https://api.vk.com/method/"
AUTH_BASE_URL = "https://oauth.vk.com/authorize?"
APP_ID = "4169750"
CAPTCHA_ENTER_RETRIES = 3
DEFAULT_SETTINGS_FILE = "settings.json"
DEFAULT_API_VERSION = "5.52"
DEFAULT_SETTINGS = {"access_token": ""}
DEFAULT_PERMISSIONS = ("friends", "photos", "audio", "video", "status",
                       "wall", "messages",)
MAX_ALBUM_UPLOAD_IMAGES = 5
MAX_WALL_UPLOAD_IMAGES = 6

AUTH_ERROR_CODE = 5
CAPTCHA_ERROR_CODE = 14

METHOD_DOMAINS = {"users", "auth", "wall", "photos", "friends", "widgets",
                  "storage", "status", "audio", "pages", "groups", "board",
                  "video", "notes", "places", "account", "messages",
                  "newsfeed", "likes", "polls", "docs", "fave",
                  "notifications", "stats", "search", "apps", "utils",
                  "database", "gifts", "execute", "market"}
