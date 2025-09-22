from rest_framework import permissions


class IsEmailVerified(permissions.BasePermission):
    """
    Permiso personalizado para verificar que el usuario tenga email verificado
    """
    message = 'Debes verificar tu email antes de acceder a esta funcionalidad.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.email_verified
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo al propietario editar
    """
    
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura para cualquier request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permisos de escritura solo para el propietario
        return obj == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo al propietario o admin acceder
    """
    
    def has_object_permission(self, request, view, obj):
        return (
            obj == request.user or 
            request.user.is_staff or 
            request.user.is_superuser
        )


class IsVerifiedEmailUser(permissions.BasePermission):
    """
    Permiso que combina autenticación y email verificado
    """
    message = 'Necesitas estar logueado y tener tu email verificado.'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.email_verified or request.user.is_social_user)
        )


class IsAdminOrSelf(permissions.BasePermission):
    """
    Permite acceso al admin o al propio usuario
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_staff or 
            request.user.is_superuser or 
            obj.id == request.user.id
        )