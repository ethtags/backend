# backend

## Installation
1. Clone the repo  
2. Run the build script: `./build.sh`

## Notes
Never use the `dev.env` file in production.  
In production, make sure to set the environment variables on the command line, or create a .env file with the appropriate values before running the `build.sh` script.  

When inserting validation logic in models, you must override the model's `save` method and call `self.full_clean` in it.  
Put all validation logic inside the model's `clean` method, and put all unique constraint validation inside the model's `validate_unique` method.  
I found that's the best way to enforce validation logic for API users going through the views/serializers, as well as developers interacting with the code directly.  

Do not do bulk updates with a queryset, i.e. Queryset.update unless you really know what you're doing.  
Meaning, you understand that the bulk update skips the model's `save` method completely and does not do any validation. So if you do it, you better be bulk updating with the correct values that obey all validation logic.  
