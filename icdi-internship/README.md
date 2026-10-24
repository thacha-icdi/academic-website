# ICDI Internship Portal
Website: https://thacha-icdi.github.io/academic-website/icdi-internship/

## Activate real accounts and shared records
1. Create a Supabase project.
2. In SQL Editor, execute schema.sql once.
3. Enable email confirmation in Authentication settings. Set minimum password length to 9. Restrict signup email domains to cmu.ac.th in server-side authentication settings or a Before User Created hook; frontend domain validation is only a convenience.
4. Set Authentication Site URL and allowed redirect URL to the website URL above.
5. Edit config.js: enter Project URL and public anon key. Never enter service_role or secret keys.
6. Register and confirm a coordinator account, then insert its Auth user UUID into public.staff using SQL Editor. Students cannot grant themselves coordinator rights.
7. Coordinator logs in and publishes real internship positions.

## Included
Responsive Thai student registration/login, confirmed-email authentication, full internship profile, opportunity search, duplicate-protected applications, application status/feedback, approved-placement work logs, report links, coordinator application review and job publishing. All shared data is protected by database row-level security. No accounts, passwords or student profiles are stored in browser localStorage by application code. Supabase manages authentication sessions.

## Acceptance checks before student launch
Use two student accounts and one coordinator. Verify email confirmation, complete profiles, apply, reject duplicate applications, verify one student cannot read another student's profile/applications/logs through the API, approve placement as coordinator, submit log as its owner. Verify unauthenticated inserts and self-assigned staff access fail.
The UI is deployed as static source; end-to-end authentication and database checks require project configuration.

## Scope
No real vacancies or institutional deadlines have been invented. Documents are permission-controlled external links, not uploaded files. Company accounts, email notifications, supervisor evaluations, password reset UI, exports and formal CMU single sign-on are future additions. Coordinator can review student profiles and update application statuses; daily log review UI is not yet included. Before collecting data, ICDI should supply the approved privacy notice, retention period and operational contact.
