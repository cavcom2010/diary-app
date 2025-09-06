"""
Email service utilities for the diary application.
Handles email sending with SendGrid integration.
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def get_domain(request=None):
    """Get the current domain for email links"""
    if request:
        return get_current_site(request).domain
    return 'localhost:8000'  # Fallback for testing


def send_welcome_email(user, request=None):
    """
    Send a welcome email to a newly registered user.
    
    Args:
        user: Django User instance
        request: HttpRequest object (optional, for domain detection)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        domain = get_domain(request)
        
        # Prepare email context
        context = {
            'user': user,
            'domain': domain,
            'protocol': 'https' if request and request.is_secure() else 'http',
        }
        
        # Render email templates
        subject = f'Welcome to My Diary, {user.first_name or user.username}!'
        text_content = render_to_string('emails/welcome_email.txt', context)
        html_content = render_to_string('emails/welcome_email.html', context)
        
        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Welcome email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, token, uid, request=None):
    """
    Send a password reset email to the user.
    This integrates with Django's built-in password reset functionality.
    
    Args:
        user: Django User instance
        token: Password reset token
        uid: User ID encoded for URL
        request: HttpRequest object (optional, for domain detection)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        domain = get_domain(request)
        
        # Prepare email context
        context = {
            'user': user,
            'domain': domain,
            'protocol': 'https' if request and request.is_secure() else 'http',
            'uid': uid,
            'token': token,
        }
        
        # Render email templates
        subject = 'Reset Your My Diary Password'
        text_content = render_to_string('emails/password_reset_email.txt', context)
        html_content = render_to_string('emails/password_reset_email.html', context)
        
        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Password reset email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def send_simple_email(subject, message, recipient_list, html_message=None):
    """
    Send a simple email using Django's send_mail function.
    
    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient emails
        html_message: Optional HTML version of the message
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Simple email sent successfully to {recipient_list}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send simple email to {recipient_list}: {str(e)}")
        return False


def test_sendgrid_connection():
    """
    Test the SendGrid connection by sending a test email to the admin.
    
    Returns:
        bool: True if test email was sent successfully, False otherwise
    """
    try:
        if not settings.SENDGRID_API_KEY:
            logger.warning("SendGrid API key not configured")
            return False
            
        success = send_simple_email(
            subject='SendGrid Test Email - My Diary',
            message='This is a test email to verify SendGrid integration is working correctly.',
            recipient_list=[settings.ADMIN_EMAIL],
            html_message='''
            <h2>SendGrid Test Email</h2>
            <p>This is a test email to verify SendGrid integration is working correctly.</p>
            <p><strong>✅ SendGrid is configured and working!</strong></p>
            '''
        )
        
        if success:
            logger.info("SendGrid connection test successful")
        else:
            logger.error("SendGrid connection test failed")
            
        return success
        
    except Exception as e:
        logger.error(f"SendGrid connection test error: {str(e)}")
        return False