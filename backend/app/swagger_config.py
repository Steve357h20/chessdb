from flasgger import Swagger

swagger_template = {
    "info": {
        "title": "Chess Data Management API",
        "description": "国际象棋数据管理系统API文档",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header"
        }
    }
}


def setup_swagger(app):
    swagger = Swagger(app, template=swagger_template)
    return swagger
