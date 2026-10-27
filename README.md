# JobLink Africa — GitHub Pages + Supabase Admin Dashboard

This project is a static website for GitHub Pages with a cloud-backed job manager using Supabase Auth + PostgreSQL. It includes public search/filtering, an admin login, add/edit/publish/draft/expire/delete controls, and Row Level Security (RLS).

## Files
- `index.html` — public job website.
- `admin.html` — private admin sign-in and dashboard (also linked from the site header).
- `assets/config.js` — paste your Supabase project URL and public anon/publishable key here.
- `assets/app.js` — public listing display and search.
- `assets/admin.js` — authenticated job management.
- `assets/admin.css` — dashboard layout.
- `supabase/schema.sql` — database tables, indexes and security policies.

## Setup (about 20–30 minutes)

### 1. Create a Supabase project
1. Go to https://supabase.com/ and create/sign in to your account.
2. Create a new project and keep the database password somewhere private.
3. Wait until the project finishes provisioning.
4. In the project, open **SQL Editor** → **New query**.
5. Open `supabase/schema.sql` from this folder, copy all its contents into the SQL Editor, and click **Run**.
6. Open **Project Settings → API** (or **Connect**, depending on the dashboard layout). Copy the **Project URL** and the public **anon / publishable key**.

### 2. Configure the website
1. Open `assets/config.js` in a text editor.
2. Replace `PASTE_YOUR_SUPABASE_PROJECT_URL_HERE` with your Supabase Project URL.
3. Replace `PASTE_YOUR_SUPABASE_ANON_OR_PUBLISHABLE_KEY_HERE` with the public anon/publishable key.
4. Save the file.

The URL and anon/publishable key are intended for browser use. **Never paste a `service_role` or secret key into this file or commit it to GitHub.** The database security depends on the RLS policies in the supplied SQL.

### 3. Create the administrator account securely
1. In Supabase, open **Authentication → Users** and choose **Add user** / **Create new user**.
2. Enter the administrator email and a strong unique password. Confirm/create the user as prompted. Do not enable public sign-ups for this website; the admin page has no sign-up form.
3. Copy the user's UUID from the Users list/details.
4. In **SQL Editor**, run the following statement after replacing the UUID with that exact user's UUID:

```sql
insert into public.admin_users (user_id)
values ('PASTE-ADMIN-USER-UUID-HERE')
on conflict (user_id) do nothing;
```

Only user IDs in `admin_users` have job-management permission. If a user can sign in but cannot manage jobs, verify the UUID was inserted correctly. To remove admin access, delete that user's row from `public.admin_users` in SQL Editor.

### 4. Test before publishing
1. Open `index.html` locally or use GitHub Pages after deploying (see below). Browser `file://` behavior can vary, so GitHub Pages is recommended for final testing.
2. Open `admin.html`, sign in with the admin email/password, and add a test listing with a valid `https://` application URL.
3. Choose **Draft** and save: it should not appear publicly.
4. Change the job to **Publish on website** and save: it should appear on the home page after refresh.
5. Test editing, unpublishing, deleting and deadlines. Remove test data before launch.

### 5. Deploy to GitHub Pages
1. Create a public repository, e.g. `joblink-africa`.
2. Upload the *contents* of this folder (including `assets/` and `supabase/`), not the ZIP itself.
3. Commit to the `main` branch.
4. Go to **Settings → Pages → Deploy from a branch → main → /(root) → Save**.
5. Wait for GitHub Pages to publish. Your public site will be `https://YOUR-USERNAME.github.io/joblink-africa/`; the admin page is `https://YOUR-USERNAME.github.io/joblink-africa/admin.html`.
6. In Supabase **Authentication → URL Configuration**, add your GitHub Pages site URL to the allowed redirect URLs if prompted. Password sign-in normally works without email redirects, but correct site URLs help with auth settings.

## Important security notes
- The admin page URL is not itself secret. Security is enforced by Supabase Auth and database RLS.
- Never use the Supabase service-role/secret key in browser code.
- Use a strong, unique password and enable MFA for your Supabase account where available.
- Avoid shared computers for admin work; sign out when finished.
- The SQL policies allow public visitors to read only published jobs whose deadlines have not passed. Drafts and expired jobs are not public.
- Supabase's public anon/publishable key is designed to be used in browser apps; the key is not a substitute for RLS.
- This project uses a third-party Supabase JS library from jsDelivr. A network connection is required for cloud database and authentication features.
- The admin can set a listing's status to `expired`. Listings past their deadline are also hidden from the public website automatically, even if their stored status remains `published`.

## Before launch
Replace the placeholder contact email (`hello@example.com`), update privacy/terms pages for your actual practices, remove fictional DEMO listings once Supabase is configured, and publish only verified vacancies with official application URLs. Never charge applicants for guaranteed jobs or visas.

## Troubleshooting
- **Dashboard says setup required:** check `assets/config.js` and save the actual Project URL + anon/publishable key.
- **Invalid login:** create the user in Supabase Authentication → Users; this page does not offer sign-up.
- **Sign-in works but job access fails:** insert the exact auth user UUID into `public.admin_users` and confirm `supabase/schema.sql` ran successfully.
- **Jobs do not show publicly:** ensure status is `published`, the deadline is blank or not past, and Supabase URL/key are correct. Check browser developer console for connection errors.
- **Permission denied:** confirm RLS is enabled and the supplied SQL policies exist. Do not solve this by exposing the service-role key.
