# Generate Client Secret
To generate a `client_secret.json` file, you need to create OAuth 2.0 credentials in the Google Cloud Console. Follow these steps:

### Create a Project in Google Cloud Console:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click on the project dropdown at the top left of the page and select "New Project".
3. Enter a name for your project and click "Create".

### Enable the Google Calendar API:
1. With your project selected, go to the API & Services Dashboard.
2. Click "Enable APIs and Services" at the top.
3. Search for "Google Calendar API" and click on it.
4. Click the "Enable" button.

### Create OAuth 2.0 Credentials:
1. Go to the [Credentials page](https://console.cloud.google.com/apis/credentials) in the Cloud Console.
2. Click "Create Credentials" and select "OAuth client ID".
3. If you haven't set up the OAuth consent screen yet, you will be prompted to do so. Fill in the required information and save.
4. Choose "Application type" as "Desktop app".
5. Enter a name for your OAuth 2.0 client and click "Create".
6. A dialog will appear showing your client ID and client secret. Click "Download" to get the `client_secret.json` file.

### Place the `client_secret.json` File in Your Project Directory:
Move the downloaded `client_secret.json` file to the directory where your script is located.

# Configure OAuth Consent Screen
To set access privileges for your Google Calendar API, you'll need to configure the OAuth consent screen and set the appropriate scopes for your application. Here's how you can manage these settings:

### Go to the OAuth Consent Screen:
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to API & Services > OAuth consent screen.

### Configure the Consent Screen:
1. Select your user type (e.g., Internal or External) and click "Create".
2. Fill in the required fields such as App name, User support email, and Developer contact information.
3. In the Scopes for Google APIs section, add the required scopes. For the Google Calendar API, you'll typically use:
    - `https://www.googleapis.com/auth/calendar` for full access to the calendar.
    - `https://www.googleapis.com/auth/calendar.readonly` for read-only access.
4. Save and continue through the remaining steps to complete the configuration.

# Managing Permission and Access
### Granting Access:
When you run your application for the first time, you'll be prompted to grant access to the specified Google account. This will open a browser window where you log in and grant access.

### Token Storage:
The credentials are stored in a file (e.g., `token.pickle`) so that you don't have to authenticate each time you run your application. Ensure this file is kept secure.

### Scope Management:
Adjust the scopes in the SCOPES list according to the level of access you need (read-only vs. full access).
