from django.urls import path
from .views import ProfileView, EmailChangeRequestView, EmailChangeVerifyView,AddressView, GiftCardView, SavedUPIView, SavedCardView, OrdersView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/email/change-request/', EmailChangeRequestView.as_view(), name='email-change-request'),
    path('profile/email/verify/', EmailChangeVerifyView.as_view(), name='email-change-verify'),
    path('profile/addresses/', AddressView.as_view(), name='addresses'),
    path('profile/gift-cards/', GiftCardView.as_view(), name='gift-cards'),
    path('profile/saved-upi/', SavedUPIView.as_view(), name='saved-upi'),
    path('profile/saved-cards/', SavedCardView.as_view(), name='saved-cards'),
    path('profile/orders/', OrdersView.as_view(), name='orders'),
]