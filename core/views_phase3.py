"""
Phase 3: E-Commerce & Payment Integration Views
Handles package purchasing, shopping cart, checkout, and payment processing
"""

import json
import stripe
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import FormView

from .models import (
    LegalPackage, ShoppingCart, CartItem, Order, OrderItem, 
    Coupon, PaymentIntent, PackageSubscription
)
from .forms import CheckoutForm, CouponForm

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


class PackageShowcaseView(ListView):
    """
    Enhanced package showcase for purchasing
    Displays packages with purchase options and detailed information
    """
    model = LegalPackage
    template_name = 'core/package_showcase.html'
    context_object_name = 'packages'
    
    def get_queryset(self):
        return LegalPackage.objects.filter(is_active=True).order_by('sort_order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's current subscriptions if authenticated
        if self.request.user.is_authenticated:
            user_packages = PackageSubscription.objects.filter(
                user=self.request.user,
                is_active=True,
                expires_at__gt=timezone.now()
            ).values_list('package_id', flat=True)
            context['user_packages'] = list(user_packages)
        else:
            context['user_packages'] = []
        
        # Get shopping cart item count
        cart = self.get_or_create_cart()
        context['cart_item_count'] = cart.item_count if cart else 0
        
        # Get featured packages
        context['featured_packages'] = self.get_queryset().filter(is_featured=True)[:3]
        
        return context
    
    def get_or_create_cart(self):
        """Get or create shopping cart for current user/session"""
        if self.request.user.is_authenticated:
            cart, created = ShoppingCart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = ShoppingCart.objects.get_or_create(session_key=session_key)
        return cart


class PackageDetailView(DetailView):
    """
    Detailed package information with purchase options
    """
    model = LegalPackage
    template_name = 'core/package_detail.html'
    context_object_name = 'package'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        package = self.get_object()
        
        # Check if user already has this package
        if self.request.user.is_authenticated:
            context['user_has_package'] = package.user_has_access(self.request.user)
        else:
            context['user_has_package'] = False
        
        # Get related packages
        context['related_packages'] = LegalPackage.objects.filter(
            is_active=True
        ).exclude(id=package.id).order_by('sort_order')[:3]
        
        # Get package content samples
        context['sample_content'] = package.get_content_by_type('article')[:3]
        
        return context


class ShoppingCartView(TemplateView):
    """
    Display shopping cart contents
    """
    template_name = 'core/shopping_cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_or_create_cart()
        
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('package').all() if cart else []
        context['total_price'] = cart.total_price if cart else Decimal('0.00')
        
        return context
    
    def get_or_create_cart(self):
        """Get or create shopping cart for current user/session"""
        if self.request.user.is_authenticated:
            cart, created = ShoppingCart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = ShoppingCart.objects.get_or_create(session_key=session_key)
        return cart


@require_POST
def add_to_cart(request, package_id):
    """
    Add package to shopping cart
    """
    try:
        package = get_object_or_404(LegalPackage, id=package_id, is_active=True)
        
        # Check if user already has this package
        if request.user.is_authenticated and package.user_has_access(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Du har allerede tilgang til denne pakken.'
            })
        
        # Get or create cart
        if request.user.is_authenticated:
            cart, created = ShoppingCart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart, created = ShoppingCart.objects.get_or_create(session_key=session_key)
        
        # Add package to cart (or update quantity)
        cart_item = cart.add_package(package)
        
        return JsonResponse({
            'success': True,
            'message': f'"{package.name}" lagt til i handlekurv.',
            'cart_item_count': cart.item_count,
            'cart_total': str(cart.total_price)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Det oppstod en feil. Prøv igjen senere.'
        })


@require_POST
def remove_from_cart(request, package_id):
    """
    Remove package from shopping cart
    """
    try:
        package = get_object_or_404(LegalPackage, id=package_id)
        
        # Get cart
        if request.user.is_authenticated:
            cart = ShoppingCart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            cart = ShoppingCart.objects.filter(session_key=session_key).first() if session_key else None
        
        if cart:
            cart.remove_package(package)
        
        return JsonResponse({
            'success': True,
            'message': f'"{package.name}" fjernet fra handlekurv.',
            'cart_item_count': cart.item_count if cart else 0,
            'cart_total': str(cart.total_price) if cart else '0.00'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Det oppstod en feil. Prøv igjen senere.'
        })


@require_POST
def apply_coupon(request):
    """
    Apply coupon code to cart
    """
    try:
        coupon_code = request.POST.get('coupon_code', '').strip().upper()
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'error': 'Vennligst oppgi en kupongkode.'
            })
        
        # Get cart
        if request.user.is_authenticated:
            cart = ShoppingCart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            cart = ShoppingCart.objects.filter(session_key=session_key).first() if session_key else None
        
        if not cart or cart.item_count == 0:
            return JsonResponse({
                'success': False,
                'error': 'Handlekurven er tom.'
            })
        
        # Validate coupon
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Ugyldig kupongkode.'
            })
        
        if not coupon.is_valid:
            return JsonResponse({
                'success': False,
                'error': 'Kupongen er utløpt eller ikke aktiv.'
            })
        
        if request.user.is_authenticated and not coupon.can_be_used_by_user(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Du har allerede brukt denne kupongen.'
            })
        
        # Calculate discount
        cart_total = cart.total_price
        discount_amount = coupon.calculate_discount(cart_total)
        
        if discount_amount == 0:
            return JsonResponse({
                'success': False,
                'error': f'Minimumsbeløp for denne kupongen er {coupon.minimum_order_amount} kr.'
            })
        
        # Store coupon in session
        request.session['applied_coupon'] = {
            'code': coupon.code,
            'discount_amount': str(discount_amount),
            'final_total': str(cart_total - discount_amount)
        }
        
        return JsonResponse({
            'success': True,
            'message': f'Kupong "{coupon.code}" anvendt!',
            'discount_amount': str(discount_amount),
            'final_total': str(cart_total - discount_amount)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Det oppstod en feil. Prøv igjen senere.'
        })


@method_decorator(login_required, name='dispatch')
class CheckoutView(FormView):
    """
    Checkout process for purchasing packages
    """
    template_name = 'core/checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy('core:payment_success')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if cart has items
        cart = self.get_cart()
        if not cart or cart.item_count == 0:
            messages.warning(request, 'Handlekurven din er tom.')
            return redirect('core:package_showcase')
        return super().dispatch(request, *args, **kwargs)
    
    def get_cart(self):
        """Get current user's cart"""
        return ShoppingCart.objects.filter(user=self.request.user).first()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart()
        
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('package').all()
        context['subtotal'] = cart.total_price
        
        # Apply coupon if present
        applied_coupon = self.request.session.get('applied_coupon')
        if applied_coupon:
            context['applied_coupon'] = applied_coupon
            context['discount_amount'] = Decimal(applied_coupon['discount_amount'])
            context['final_total'] = Decimal(applied_coupon['final_total'])
        else:
            context['discount_amount'] = Decimal('0.00')
            context['final_total'] = cart.total_price
        
        # Stripe publishable key
        context['stripe_publishable_key'] = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
        
        return context
    
    def get_initial(self):
        """Pre-fill form with user data"""
        user = self.request.user
        return {
            'billing_name': user.get_full_name(),
            'billing_email': user.email,
            'billing_organization': getattr(user, 'organization', ''),
        }
    
    def form_valid(self, form):
        """Process checkout and create Stripe payment intent"""
        try:
            with transaction.atomic():
                cart = self.get_cart()
                
                # Calculate totals
                subtotal = cart.total_price
                applied_coupon = self.request.session.get('applied_coupon')
                discount_amount = Decimal(applied_coupon['discount_amount']) if applied_coupon else Decimal('0.00')
                final_amount = subtotal - discount_amount
                
                # Create order
                order = Order.objects.create(
                    user=self.request.user,
                    total_amount=subtotal,
                    discount_amount=discount_amount,
                    final_amount=final_amount,
                    billing_name=form.cleaned_data['billing_name'],
                    billing_email=form.cleaned_data['billing_email'],
                    billing_organization=form.cleaned_data.get('billing_organization', ''),
                    billing_address=form.cleaned_data.get('billing_address', ''),
                    billing_city=form.cleaned_data.get('billing_city', ''),
                    billing_postal_code=form.cleaned_data.get('billing_postal_code', ''),
                    customer_notes=form.cleaned_data.get('customer_notes', ''),
                    coupon_code=applied_coupon['code'] if applied_coupon else '',
                )
                
                # Create order items
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        package=cart_item.package,
                        quantity=cart_item.quantity,
                        price=cart_item.price
                    )
                
                # Create Stripe payment intent
                intent = stripe.PaymentIntent.create(
                    amount=int(final_amount * 100),  # Convert to cents
                    currency='nok',
                    metadata={
                        'order_id': str(order.id),
                        'order_number': order.order_number,
                        'user_id': str(self.request.user.id),
                    }
                )
                
                # Save payment intent
                order.stripe_payment_intent_id = intent.id
                order.save()
                
                PaymentIntent.objects.create(
                    stripe_payment_intent_id=intent.id,
                    order=order,
                    amount=int(final_amount * 100),
                    status=intent.status
                )
                
                # Store order ID in session
                self.request.session['pending_order_id'] = str(order.id)
                self.request.session['client_secret'] = intent.client_secret
                
                # Clear applied coupon
                if 'applied_coupon' in self.request.session:
                    del self.request.session['applied_coupon']
                
                return redirect('core:payment_processing')
                
        except Exception as e:
            messages.error(self.request, 'Det oppstod en feil under behandling av bestillingen. Prøv igjen.')
            return self.form_invalid(form)


class PaymentProcessingView(LoginRequiredMixin, TemplateView):
    """
    Payment processing page with Stripe Elements
    """
    template_name = 'core/payment_processing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        order_id = self.request.session.get('pending_order_id')
        client_secret = self.request.session.get('client_secret')
        
        if not order_id or not client_secret:
            raise Http404('Ingen ventende bestilling funnet.')
        
        try:
            order = Order.objects.get(id=order_id, user=self.request.user)
        except Order.DoesNotExist:
            raise Http404('Bestilling ikke funnet.')
        
        context['order'] = order
        context['client_secret'] = client_secret
        context['stripe_publishable_key'] = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
        
        return context


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhooks
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle specific events
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_payment_success(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_failure(payment_intent)
    
    return HttpResponse(status=200)


def handle_payment_success(payment_intent):
    """
    Handle successful payment
    """
    try:
        # Get order from metadata
        order_id = payment_intent['metadata'].get('order_id')
        if not order_id:
            return
        
        order = Order.objects.get(id=order_id)
        
        # Update order status
        order.mark_as_paid()
        
        # Update payment intent record
        PaymentIntent.objects.filter(
            stripe_payment_intent_id=payment_intent['id']
        ).update(
            status=payment_intent['status'],
            payment_method_type=payment_intent.get('charges', {}).get('data', [{}])[0].get('payment_method_details', {}).get('type', ''),
            webhook_data=payment_intent
        )
        
        # Clear user's cart
        ShoppingCart.objects.filter(user=order.user).delete()
        
        # Use coupon if applied
        if order.coupon_code:
            try:
                coupon = Coupon.objects.get(code=order.coupon_code)
                coupon.use_coupon()
            except Coupon.DoesNotExist:
                pass
        
    except Order.DoesNotExist:
        pass
    except Exception as e:
        # Log error
        pass


def handle_payment_failure(payment_intent):
    """
    Handle failed payment
    """
    try:
        order_id = payment_intent['metadata'].get('order_id')
        if not order_id:
            return
        
        order = Order.objects.get(id=order_id)
        order.payment_status = 'failed'
        order.save()
        
        PaymentIntent.objects.filter(
            stripe_payment_intent_id=payment_intent['id']
        ).update(
            status=payment_intent['status'],
            webhook_data=payment_intent
        )
        
    except Order.DoesNotExist:
        pass
    except Exception as e:
        # Log error
        pass


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    """
    Payment success confirmation page
    """
    template_name = 'core/payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get most recent paid order
        order = Order.objects.filter(
            user=self.request.user,
            payment_status='succeeded'
        ).order_by('-paid_at').first()
        
        context['order'] = order
        return context


class OrderHistoryView(LoginRequiredMixin, ListView):
    """
    User's order history
    """
    model = Order
    template_name = 'core/order_history.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    Detailed view of a specific order
    """
    model = Order
    template_name = 'core/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context['order_items'] = order.items.select_related('package').all()
        return context


@require_http_methods(['GET'])
def cart_count(request):
    """
    AJAX endpoint to get current cart item count
    """
    if request.user.is_authenticated:
        cart = ShoppingCart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        cart = ShoppingCart.objects.filter(session_key=session_key).first() if session_key else None
    
    count = cart.item_count if cart else 0
    
    return JsonResponse({'count': count})
