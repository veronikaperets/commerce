from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from .models import User, Listing, Bid, Comment
from django import forms
from django.shortcuts import get_object_or_404


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'start_bid', 'image_url', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'category': forms.Select(choices=[('', '-- Select Category --'), ('Fashion', 'Fashion'), ('Toys', 'Toys'), ('Electronics', 'Electronics'), ('Home', 'Home')])
        }

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid_amount']
        widgets = {
            'bid_amount': forms.NumberInput(attrs={'min': 0, 'step': '0.01'})
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment_text']
        widgets = {
            'comment_text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add your comment here...'})
        }



def index(request):
    listings = Listing.objects.filter(is_active=True)
    return render(request, "auctions/index.html", {"listings": listings})



def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    

def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)

        if form.is_valid():
            new_listing = form.save(commit=False)  # Don't save it yet
            new_listing.user = request.user  # Add the current user
            new_listing.current_bid = new_listing.start_bid  # set the current bid to the starting bid
            new_listing.save()  # Now save
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/create_listing.html", {"form": form, "message": "Please correct the errors below."})

    form = ListingForm()
    return render(request, "auctions/create_listing.html", {"form": form})


def listing_page(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    return render(request, "auctions/listing_page.html", {"listing": listing})

def add_to_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    request.user.watchlist.add(listing)
    return HttpResponseRedirect(reverse('listing_page', args=[listing_id]))

def remove_from_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    request.user.watchlist.remove(listing)
    return HttpResponseRedirect(reverse('listing_page', args=[listing_id]))

def place_bid(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    # Handle the bid
    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            new_bid = form.cleaned_data["bid_amount"]
            
            if new_bid >= listing.start_bid and new_bid > listing.highest_bid():
                bid = Bid(listing=listing, user=request.user, bid_amount=new_bid)
                bid.save()
                # Update the current_bid of the listing
                listing.current_bid = new_bid
                listing.save()
                return HttpResponseRedirect(reverse('listing_page', args=[listing_id]))
            else:
                error = "Your bid must be greater than the current highest bid and at least equal to the starting bid."
        else:
            error = "Invalid bid."
        return render(request, "auctions/listing_page.html", {"listing": listing, "bid_error": error})

    return HttpResponseRedirect(reverse('listing_page', args=[listing_id]))


def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Ensure the user is authenticated and is the creator of the listing
    if not request.user.is_authenticated or listing.user != request.user:
        return HttpResponseForbidden("You don't have permission to close this auction.")
    
    # Close the auction
    listing.is_active = False
    
    # Set the winner
    highest_bid = listing.bid_set.order_by('-bid_amount').first()
    if highest_bid:
        listing.winner = highest_bid.user
    
    listing.save()
    return HttpResponseRedirect(reverse('listing_page', args=[listing_id]))



def listing_page(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    comments = listing.comment_set.all()  # Get all comments for this listing

    if request.method == "POST" and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.listing = listing
            comment.save()

    form = CommentForm()  # For displaying an empty form after submission or on GET request
    return render(request, "auctions/listing_page.html", {
        "listing": listing,
        "comments": comments,
        "form": form
    })

def categories(request):
    categories = set(Listing.objects.values_list('category', flat=True))
    return render(request, "auctions/categories.html", {"categories": categories})


def category_listings(request, category_name):
    listings = Listing.objects.filter(category=category_name, is_active=True)
    return render(request, "auctions/category_listings.html", {"listings": listings, "category_name": category_name})






