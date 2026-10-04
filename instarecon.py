#!/usr/bin/env python3
"""
IG T98 OSINT PRO+ - Instagram OSINT Tool
A tool for gathering public information from Instagram profiles for penetration testing and ethical hacking.

Developed by : Team0098 (https://team0098.com)
Telegram     : @MvahyR (https://t.me/MvahyR)
License      : MIT

Based on the original InstaRecon project by Asad Faizee.
"""

import argparse
import requests
import sys
import subprocess
from urllib.parse import quote_plus
from json import dumps, decoder
import os

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing required dependencies...")
    deps = ["requests", "phonenumbers", "pycountry"]
    
    for dep in deps:
        try:
            print(f"  Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")
            return False
    
    print("✅ Dependencies installed successfully!\n")
    return True

# Try to import dependencies, install if missing
try:
    import phonenumbers
    from phonenumbers.phonenumberutil import (
        region_code_for_country_code,
        region_code_for_number,
    )
    import pycountry
except ImportError:
    print("📦 Missing dependencies detected. Installing...")
    if install_dependencies():
        import phonenumbers
        from phonenumbers.phonenumberutil import (
            region_code_for_country_code,
            region_code_for_number,
        )
        import pycountry
    else:
        print("❌ Failed to install dependencies. Please install manually:")
        print("pip install requests phonenumbers pycountry")
        sys.exit(1)


# ─────────────────────────── Display helpers ───────────────────────────
WIDTH = 64         # total width of banners, rules and section headers
LABEL_WIDTH = 25   # width of the label column in result rows


def _supports_color():
    """Enable ANSI colors only on real terminals (honors NO_COLOR)"""
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return False
    if os.name == "nt":
        os.system("")  # enables ANSI escape sequences on Windows 10+
    return True


USE_COLOR = _supports_color()


def _c(code, text):
    """Wrap text in an ANSI color code (plain text when colors are off)"""
    return "\033[{}m{}\033[0m".format(code, text) if USE_COLOR else str(text)


def _row(label, value):
    """Print one aligned 'label : value' row"""
    print("  " + _c("36", label.ljust(LABEL_WIDTH)) + ": " + str(value))


def _section(title):
    """Print a section header with a horizontal rule"""
    head = "── " + title + " "
    print("\n" + _c("1;35", head) + _c("35", "─" * (WIDTH - len(head))))


def _flag(value):
    """Colored check / cross mark"""
    return _c("32", "✓") if value else _c("31", "✗")


class IGT98OsintPro:
    def __init__(self, session_id):
        self.session_id = session_id
        self.headers = {
            "User-Agent": "Instagram 64.0.0.14.96",
            "Accept-Language": "en-US",
        }
        self.cookies = {'sessionid': self.session_id}

    def get_user_id(self, username):
        """Get user ID from username"""
        headers = {"User-Agent": "iphone_ua", "x-ig-app-id": "936619743392459"}
        
        try:
            response = requests.get(
                f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
                headers=headers,
                cookies=self.cookies,
                timeout=10
            )
            
            if response.status_code == 404:
                return {"id": None, "error": "User not found"}
            
            data = response.json()
            user_id = data["data"]['user']['id']
            return {"id": user_id, "error": None}
            
        except decoder.JSONDecodeError:
            return {"id": None, "error": "Rate limit - please wait before trying again"}
        except requests.exceptions.Timeout:
            return {"id": None, "error": "Request timeout - please try again"}
        except Exception as e:
            return {"id": None, "error": f"Error: {str(e)}"}

    def get_user_info(self, search, search_type="username"):
        """Get detailed user information"""
        if search_type == "username":
            user_data = self.get_user_id(search)
            if user_data["error"]:
                return user_data
            user_id = user_data["id"]
        else:
            try:
                user_id = str(int(search))
            except ValueError:
                return {"user": None, "error": "Invalid ID format"}

        try:
            response = requests.get(
                f'https://i.instagram.com/api/v1/users/{user_id}/info/',
                headers=self.headers,
                cookies=self.cookies,
                timeout=10
            )
            
            if response.status_code == 429:
                return {"user": None, "error": "Rate limit - please wait before trying again"}
            
            response.raise_for_status()
            
            info_user = response.json().get("user")
            if not info_user:
                return {"user": None, "error": "User not found"}
            
            info_user["userID"] = user_id
            return {"user": info_user, "error": None}
            
        except requests.exceptions.Timeout:
            return {"user": None, "error": "Request timeout - please try again"}
        except requests.exceptions.RequestException as e:
            return {"user": None, "error": f"Request failed: {str(e)}"}

    def advanced_lookup(self, username):
        """Get obfuscated login information"""
        data = "signed_body=SIGNATURE." + quote_plus(dumps(
            {"q": username, "skip_recovery": "1"},
            separators=(",", ":")
        ))
        
        headers = {
            "Accept-Language": "en-US",
            "User-Agent": "Instagram 101.0.0.15.120",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-IG-App-ID": "124024574287414",
            "Accept-Encoding": "gzip, deflate",
            "Host": "i.instagram.com",
            "Connection": "keep-alive",
            "Content-Length": str(len(data))
        }
        
        try:
            response = requests.post(
                'https://i.instagram.com/api/v1/users/lookup/',
                headers=headers,
                data=data,
                timeout=10
            )
            return {"user": response.json(), "error": None}
        except decoder.JSONDecodeError:
            return {"user": None, "error": "rate limit"}
        except requests.exceptions.Timeout:
            return {"user": None, "error": "timeout"}

    def format_phone_number(self, country_code, phone_number):
        """Format phone number with country information"""
        phonenr = f"+{country_code} {phone_number}"
        try:
            pn = phonenumbers.parse(phonenr)
            countrycode = region_code_for_country_code(pn.country_code)
            country = pycountry.countries.get(alpha_2=countrycode)
            if country:
                phonenr = f"{phonenr} ({country.name})"
        except:
            pass
        return phonenr

    def safe_get(self, data, key, default="N/A"):
        """Safely get a value from dictionary"""
        return data.get(key, default)

    def display_banner(self):
        """Display tool banner"""
        inner = WIDTH - 2
        lines = [
            "IG T98 OSINT PRO+",
            "Instagram OSINT Tool",
            "",
            "For Penetration Testing & Ethical Hacking",
            "Team0098  |  team0098.com  |  Telegram: @MvahyR",
        ]
        print()
        print(_c("35", "╔" + "═" * inner + "╗"))
        for i, line in enumerate(lines):
            style = "1;37" if i == 0 else ("36" if i == 1 else "37")
            print(_c("35", "║") + _c(style, line.center(inner)) + _c("35", "║"))
        print(_c("35", "╚" + "═" * inner + "╝"))
        print()

    def display_results(self, info):
        """Display formatted user information"""
        print("\n" + _c("35", "═" * WIDTH))
        print(_c("1", "  INSTAGRAM RECONNAISSANCE RESULTS"))
        print(_c("35", "═" * WIDTH))
        
        # Basic Information & Account Status
        _section("PROFILE")
        _row("Username", self.safe_get(info, 'username'))
        _row("User ID", self.safe_get(info, 'userID'))
        _row("Full Name", self.safe_get(info, 'full_name'))
        
        is_verified = self.safe_get(info, 'is_verified', False)
        is_business = self.safe_get(info, 'is_business', False)
        _row("Verified Account", _flag(is_verified))
        _row("Business Account", _flag(is_business))
        _row("Private Account", _flag(self.safe_get(info, 'is_private', False)))
        
        # Additional account info
        additional_info = []
        if info.get('is_whatsapp_linked'):
            additional_info.append("WhatsApp Linked")
        if info.get('is_memorialized'):
            additional_info.append("Memorial Account")
        if info.get('is_new_to_instagram'):
            additional_info.append("New User")
        
        if additional_info:
            _row("Account Flags", ', '.join(additional_info))
        
        # Statistics
        followers = self.safe_get(info, 'follower_count', 0)
        following = self.safe_get(info, 'following_count', 0)
        posts = self.safe_get(info, 'media_count', 0)
        
        _section("ENGAGEMENT METRICS")
        _row("Followers", f"{followers:,}")
        _row("Following", f"{following:,}")
        _row("Posts", f"{posts:,}")
        
        # Calculate engagement ratio if applicable
        if followers > 0:
            ratio = following / followers
            _row("Following/Follower Ratio", f"{ratio:.2f}")
        
        # IGTV posts (if available)
        if 'total_igtv_videos' in info:
            _row("IGTV Posts", info['total_igtv_videos'])
        
        # Optional fields
        if info.get("external_url"):
            _section("EXTERNAL LINKS")
            _row("Website", info['external_url'])
        
        # Biography
        if info.get("biography"):
            bio_lines = info["biography"].split("\n")
            _section("BIOGRAPHY")
            for line in bio_lines:
                if line.strip():
                    print("  " + line)
        
        # Contact Information
        contact_found = False
        if info.get("public_email"):
            if not contact_found:
                _section("PUBLIC CONTACT INFO")
                contact_found = True
            _row("Email", info['public_email'])
        
        if info.get("public_phone_number"):
            if not contact_found:
                _section("PUBLIC CONTACT INFO")
                contact_found = True
            phone = self.format_phone_number(
                info.get("public_phone_country_code", ""),
                info["public_phone_number"]
            )
            _row("Phone", phone)
        
        # Profile Picture
        profile_pic_url = None
        if 'hd_profile_pic_url_info' in info and info['hd_profile_pic_url_info'].get('url'):
            profile_pic_url = info['hd_profile_pic_url_info']['url']
        elif 'profile_pic_url_hd' in info:
            profile_pic_url = info['profile_pic_url_hd']
        elif 'profile_pic_url' in info:
            profile_pic_url = info['profile_pic_url']
        
        if profile_pic_url:
            _section("PROFILE MEDIA")
            _row("Profile Picture", profile_pic_url)
        
        # Advanced lookup
        _section("ADVANCED RECONNAISSANCE")
        
        other_info = self.advanced_lookup(info["username"])
        
        if other_info["error"] == "rate limit":
            print("  ⚠️  Rate limit reached - please wait before trying again")
        elif other_info["error"] == "timeout":
            print("  ⚠️  Request timeout - please try again later")
        elif other_info["user"] and "message" in other_info["user"]:
            if other_info["user"]["message"] == "No users found":
                print("  No additional reconnaissance data available")
            else:
                _row("Status", other_info['user']['message'])
        elif other_info["user"]:
            recon_found = False
            if other_info["user"].get("obfuscated_email"):
                _row("Obfuscated Email", other_info['user']['obfuscated_email'])
                recon_found = True
            
            if other_info["user"].get("obfuscated_phone"):
                _row("Obfuscated Phone", other_info['user']['obfuscated_phone'])
                recon_found = True
                
            if not recon_found:
                print("  No obfuscated contact information found")
        
        print("\n" + _c("35", "═" * WIDTH))
        
        # Security Note
        print("\n" + _c("33", "🔒 Security Note: This information is publicly available"))
        print("   Use responsibly and in accordance with applicable laws.")
        

def main():
    parser = argparse.ArgumentParser(
        description="IG T98 OSINT PRO+ - Instagram OSINT Tool for Penetration Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python instarecon.py -u username -s your_session_id
  python instarecon.py -i 123456789 -s your_session_id
  python instarecon.py -u username -s your_session_id --debug

Getting your Instagram session ID:
  1. Open Instagram in your browser and log in
  2. Open Developer Tools (F12)
  3. Go to Application/Storage → Cookies → https://www.instagram.com
  4. Find and copy the 'sessionid' value

⚠️  LEGAL DISCLAIMER:
This tool is for educational and authorized penetration testing purposes only.
Users are responsible for complying with applicable laws and regulations.

Developed by Team0098 | https://team0098.com | Telegram: @MvahyR
        """
    )
    
    parser.add_argument('-s', '--sessionid', help="Instagram session ID", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--username', help="Instagram username")
    group.add_argument('-i', '--id', help="Instagram user ID")
    parser.add_argument('--debug', action='store_true', help="Show debug information")
    parser.add_argument('--no-banner', action='store_true', help="Skip banner display")
    
    args = parser.parse_args()
    
    # Create IGT98OsintPro instance
    recon = IGT98OsintPro(args.sessionid)
    
    # Display banner
    if not args.no_banner:
        recon.display_banner()
    
    # Determine search type and value
    search_type = "id" if args.id else "username"
    search_value = args.id or args.username
    
    print(_c("1", f"🔍 Starting reconnaissance for {search_type}: ") + _c("36", search_value))
    print("⏳ Gathering intelligence...")
    
    # Get user information
    result = recon.get_user_info(search_value, search_type)
    
    if result.get("error"):
        print(_c("31", f"\n❌ Error: {result['error']}"))
        
        # Provide helpful suggestions
        if "Rate limit" in result['error']:
            print("\n💡 Try again in a few minutes or use a different session ID")
        elif "User not found" in result['error']:
            print("\n💡 Check the username/ID spelling and try again")
        elif "timeout" in result['error'].lower():
            print("\n💡 Check your internet connection and try again")
            
        sys.exit(1)
    
    # Display results
    recon.display_results(result["user"])
    
    # Debug information
    if args.debug:
        _section("DEBUG INFORMATION")
        print("\nAll available fields:")
        for key, value in result["user"].items():
            if not key.endswith('_url'):  # Skip URLs for cleaner output
                print(f"  {key}: {value}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        else:
            print("💡 Run with --debug flag for detailed error information")
        sys.exit(1)
