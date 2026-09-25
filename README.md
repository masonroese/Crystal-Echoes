# Crystal Echoes for Android

This folder is a complete Android project for Crystal Echoes. GitHub builds the
installable app file (an APK) for you, for free. You never need to install
Android Studio.

## One-time setup (about 10 minutes)

1. **Make a GitHub account** at https://github.com/signup (free).
2. **Create a repository**: click **+** (top right) → **New repository**.
   Name it `crystal-echoes`. Private is fine. Don't tick any of the
   "Add a README / .gitignore / license" boxes. Click **Create repository**.
3. **Upload the project**: on the new, empty repository page, click
   **uploading an existing file**. Unzip `crystal-echoes-android.zip` on your
   computer, open the unzipped folder, select **everything inside it**, and
   drag it onto the GitHub page. Wait for the files to finish uploading, then
   click **Commit changes**.
4. **Check the build started**: open the **Actions** tab. You should see
   "Build Android APK" running (a yellow dot). It takes about 5 to 10 minutes.
   - If the Actions tab says there are no workflows, the hidden `.github`
     folder didn't upload (computers often hide folders that start with a dot).
     Fix: in the Actions tab click **set up a workflow yourself**, delete the
     sample text, paste in everything from `workflow-copy.yml` (it's in this
     folder), and click **Commit changes**. The build then starts.

## Getting the app onto your phone

1. When the run shows a green tick, click it and scroll to **Artifacts**.
2. Download **crystal-echoes-apk**. It arrives as a .zip; unzip it to get
   `crystal-echoes.apk`.
   - Easiest: do this in your phone's browser while signed in to GitHub, so
     the file lands on the phone directly. Or download on your computer and
     send it to your phone (Google Drive, email, or USB cable).
3. On the phone, tap `crystal-echoes.apk`. Android will ask you to allow
   installs from that app (your browser or Files app). Allow it, then tap
   **Install**.
4. Open **Crystal Echoes** from your home screen.

Android may show a "Play Protect" warning because the app isn't from the Play
Store. That's expected for apps you build yourself; choose **Install anyway**.

## iPhone: add it to your home screen

Apple doesn't allow installing self-built app files, so on iPhone the game runs
as a home-screen web app: its own icon, full screen, and playable offline.
GitHub publishes it to a free web address for you.

One-time setup:
1. The repository must be **public** for free GitHub Pages: repository
   **Settings → General → Danger Zone → Change visibility → Public**.
2. **Settings → Pages** → under "Build and deployment", set **Source** to
   **GitHub Actions**.
3. Make sure `.github/workflows/publish-web.yml` is in the repository. If the
   hidden `.github` folder didn't upload: **Actions → New workflow → set up a
   workflow yourself**, name it `publish-web.yml`, paste in everything from
   `publish-web-copy.yml`, and **Commit changes**.
4. Open the **Actions** tab and wait for "Publish web version" to finish
   (about a minute). Click the run: the web address is shown at the top, in the
   form `https://YOUR-NAME.github.io/crystal-echoes/`.

On the iPhone:
1. Open that address in **Safari** (it must be Safari).
2. Tap **Share** (the square with an arrow) → **Add to Home Screen** → **Add**.
3. Open **Crystal Echoes** from the home screen and turn the phone sideways.

After the first launch it works without internet. When the game is updated,
open it once while online and it picks up the new version. This web address
also works on Android phones and computers.

## Controls on the phone

- The game is always sideways (landscape) and full screen.
- **Move:** put a thumb anywhere on the left half of the screen and drag.
- **Act:** touch anywhere on the right half. Hold it to draw the Ranger's bow.
- **Pause:** the II button (top right), or the phone's Back gesture.
  Back on the setup screen closes the app.

## Updating the game later

When the game changes, replace `www/index.html` in the repository (open the
file on GitHub → pencil/upload a new version → **Commit changes**). GitHub
rebuilds the APK automatically; install the new one over the old one.

## What's in here

| Path | What it is |
| --- | --- |
| `www/index.html` | The game itself (phone layout). |
| `www/fonts/` | The two typefaces, bundled so the app works offline (SIL Open Font License). |
| `resources/android/` | App icon, splash screen, and the full-screen screen setup. |
| `scripts/prepare-android.sh` | Locks landscape, applies the icon, turns on full screen. |
| `.github/workflows/build-apk.yml` | The instructions GitHub follows to build the APK. |
| `workflow-copy.yml` | A visible copy of the above, for step 4 if needed. |
| `.github/workflows/publish-web.yml` | Publishes the game to a web address for iPhone. |
| `publish-web-copy.yml` | A visible copy of the above. |
| `www/manifest.json`, `www/sw.js`, `www/icons/` | Home-screen icon and offline support. |
| `tools/` | Scripts used to make the phone layout and icons from the desktop version. |

The APK is a "debug" build: perfect for playing and sharing with friends by
file. Publishing on the Google Play Store needs a signed release build and a
Play developer account ($25 one-time); that can be added to this project later.
