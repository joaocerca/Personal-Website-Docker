from flask.cli import FlaskGroup
from logging.config import dictConfig
from project import app
from werkzeug.debug import DebuggedApplication


dictConfig(
    {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "[%(asctime)s] %(levelname)s || %(module)s >>>>>>> %(message)s",
                "datefmt": "%d %B %Y %H:%M:%S %Z",
            }
        },
        "handlers": {
            "default":{
                "level": "DEBUG",
                "formatter":"standard",
                "class": "logging.StreamHandler",
            },
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "standard",
            },
            "file":{
                "class":"logging.FileHandler",
                "filename": "flask.log",
                "formatter":"standard",
            }
        },
        "loggers":{
            "":{
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": True
                
            }
        },
        
    }
)



cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()


