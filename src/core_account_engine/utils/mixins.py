from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class PaginateModelMixin(object):
    def paginate(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            # TODO: update this!
            return "No existen resultados"


class ChangeStateMixin(object):
    """
        Mixin to make a change of state in a model,
        According to the parameter transition passed, it executes that method within the same value.
    """

    def change_state(self, transition):
        instance = self.get_object()
        instance, applied = getattr(instance, transition)()

        if not applied:
            msg = 'The {name} \"{lookup}={lookup_value}\", transition can not change to {state}'.format(
                name=instance.__class__.__name__,
                lookup=self.lookup_field,
                lookup_value=instance.id,
                state=transition
            )
            raise ValidationError({'detail': msg})

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ActionSerializerMixin(object):
    action_serializers = {}

    def get_serializer_class(self):
        if hasattr(self, 'action') and self.action in self.action_serializers:
            return self.action_serializers[self.action]

        return super().get_serializer_class()

