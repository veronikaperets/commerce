from django.contrib import admin
from .models import Listing, Comment, Bid, User  # Import your models

# Register your models with the admin site:
admin.site.register(Listing)
admin.site.register(Comment)
admin.site.register(Bid)
admin.site.register(User)
