Yeez posts to Facebook and Instagram through your own Meta app. Almost every failed connection comes from one of three settings in that app. Check all three, then click **Try again** on the error page (or ask your AI app to connect Facebook again).

## "Invalid Scopes: …"

Your Meta app is missing a permission Yeez asks for. Adding a use case doesn't always add all of its permissions, so open each one and add them yourself:

1. Go to developers.facebook.com → your app → **Use cases**.
2. Next to each use case, click **Customize**, then **Add** next to every permission below.
   - **Manage everything on your Page:** pages_show_list, pages_manage_posts, pages_read_engagement, pages_read_user_content, pages_manage_engagement, pages_manage_metadata, business_management
   - **Engage with customers on Messenger from Meta:** pages_messaging
   - **Manage messaging and content on Instagram:** instagram_basic, instagram_content_publish, instagram_manage_comments, instagram_manage_messages
3. The error names the ones that are missing. pages_manage_engagement is the one most often left out.

## "Can't load URL: The domain of this URL isn't included in the app's domains"

1. **App settings → Basic → App Domains:** add `yeez.ai` and save.
2. **Valid OAuth Redirect URIs** (under Facebook Login for Business → Settings, or the Manage everything on your Page use case → Customize → Settings): paste `https://yeez.ai/connect/meta/callback` exactly, and save.

## "This connection attempt timed out"

The attempt was left open too long or opened twice. Click **Try again**. Your saved Meta app is used again, so there's nothing to re-enter.

## Still not working

- The app must be switched from **Development** to **Live** (top of the app's page). Comment replies only work when it's Live.
- Facebook may ask for your password or passkey more than once. That's normal.
- On the selection screen, tick every Page (and its Instagram account) you want Yeez to post to.

When it works, Yeez lists each Page and Instagram account as connected.
