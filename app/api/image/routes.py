from app.api.image.facade import ImageFacade
from app.models import Image


def register_image_api_urls(app):
    registrar = app.api_url_registrar
    registrar.register_get_routes(Image, ImageFacade)
    #registrar.register_relationship_get_route(CorrespondentRoleFacade, 'roles-within-document')

    #registrar.register_post_routes(CorrespondentRole, CorrespondentRoleFacade)