# Study guide: Why new members abandon mobile account opening

**Method:** structured-interview
**Participants:** 24

## Objective
A credit union sees 38 percent of people who start opening a checking account in its mobile app stop before funding the account. This study finds out where in the account-opening flow people stop, why they stop, and what would have kept them going, so the product team can decide what to fix first. It compares people who abandoned with people who finished, and compares the mobile app with the website and the branch. Interviews are structured, by phone, 20 to 30 minutes each. This first run uses synthetic data.

## Audience
Adults who started opening a checking account with the credit union in the last 90 days, through the mobile app, the website, or in a branch. The sample includes both people who finished opening and funding the account and people who abandoned before funding, so the two groups can be compared.

## Research questions
RQ1. At which step do people abandon account opening, and what happens at that step that makes them stop?
RQ2. How do the reasons for abandoning differ between the app, the website, and the branch?
RQ3. What did people who completed the process do when they hit the same obstacles?
RQ4. What would have brought an abandoner back to finish?

## Participant criteria
### Must have
- Age 18 or older.
- Started opening a checking account with the credit union within the last 90 days.
- Started through exactly one of: the mobile app, the website, or a branch.
- Either funded the new account (completed) or stopped at any point before funding it (abandoned).
- Able to take a 20 to 30 minute phone interview in English.

### Must not have
- Employment at the credit union or a household member who works there.
- Work in banking product, UX, or user research in the last 12 months.
- Started the application more than 90 days ago.
- Was opening only a savings, loan, or business account, with no checking account.
- Took part in a credit union research study in the last 6 months.

### Segments
| Column | Values | Target |
|---|---|---|
| channel | app; web; branch | 8 each |
| outcome | completed; abandoned | 12 each (4 per channel abandoned, 4 per channel completed) |

## Questionnaire
| ID | Question | Type | Options | RQ |
|---|---|---|---|---|
| Q01 | Tell us why you decided to open a checking account with the credit union, and why you started in the app, on the website, or in a branch. | free-text | | RQ2 |
| Q02 | Which of these steps did you complete? | multi-choice | Entered personal details; Answered membership eligibility questions; Verified identity; Reviewed and accepted disclosures; Chose account options; Funded the account | RQ1 |
| Q03 | How many separate sittings or visits did you spend on the application from start to your last attempt? | numeric | | RQ1 |
| Q04 | Describe what you did when you were asked to move money into the new account, or what stopped you from getting to that point. | free-text | | RQ1 |
| Q05 | At which step did you stop, or, if you finished, at which step were you stuck the longest? | single-choice | Entering personal details; Membership eligibility questions; Identity verification; Disclosures; Choosing account options; Funding the account; Never got stuck | RQ1 |
| Q06 | Walk us through what happened at that step: what you were asked for, what you did, and what happened next. | free-text | | RQ1 |
| Q07 | Describe any time you needed a document, number, or piece of information you did not have with you. What was it, and what did you do? | free-text | | RQ2 |
| Q08 | Describe any point where something did not work the way you expected, such as an error, a rejection, a wait for review, or being told to go somewhere else. | free-text | | RQ2 |
| Q09 | Which ways did you contact the credit union for help during the application? | multi-choice | Did not contact; Phone; In-app or web chat; Secure message or email; Visited a branch | RQ3 |
| Q10 | Tell us what you did to get past the hardest step: who you asked, what you tried, and whether you switched to another device or channel. | free-text | | RQ3 |
| Q11 | How easy or hard was the account-opening process overall? | likert-5 | 1=Very hard; 2=Hard; 3=Neither; 4=Easy; 5=Very easy | RQ2 |
| Q12 | Describe what the credit union could have done at the moment you stopped or got stuck that would have kept you going. | free-text | | RQ4 |
| Q13 | What have you done about a checking account since you started this application? | single-choice | Finished with the credit union on the first try; Came back later and finished with the credit union; Opened an account elsewhere; Kept using an existing account; Have not done anything yet | RQ4 |
| Q14 | Tell us what would need to happen for you to go back and finish opening the account with the credit union. | free-text | | RQ4 |

## Anticipated tags
### step
- `step:personal-details` — answer concerns entering name, address, SSN, or contact details
- `step:eligibility` — answer concerns proving membership eligibility (employer, location, association)
- `step:id-verification` — answer concerns photographing an ID, a selfie, or identity checks
- `step:disclosures` — answer concerns reading or accepting terms and disclosures
- `step:account-options` — answer concerns choosing account type, features, or overdraft settings
- `step:funding` — answer concerns moving the first deposit into the account

### blocker
- `blocker:missing-document` — did not have a required document or number on hand
- `blocker:id-capture-failed` — ID photo or selfie was rejected or would not capture
- `blocker:technical-error` — app or site crashed, froze, timed out, or showed an error
- `blocker:manual-review` — application held for review with no clear timeline
- `blocker:external-account-link` — could not link or verify an outside bank account for funding
- `blocker:minimum-deposit` — opening deposit amount was too high or unclear
- `blocker:too-long` — process took more time or steps than expected
- `blocker:sent-elsewhere` — was told to call, visit a branch, or use another channel to continue

### workaround
- `workaround:switched-channel` — moved from app to web or branch, or the reverse
- `workaround:switched-device` — moved to another phone, tablet, or computer
- `workaround:contacted-support` — called, chatted, or messaged the credit union for help
- `workaround:retried-later` — stopped and came back in a later sitting
- `workaround:asked-someone` — got help from a friend or family member
- `workaround:alternate-funding` — funded by a different method (check, cash, transfer at branch)

### return-trigger
- `return-trigger:reminder` — a reminder message or email would have brought them back
- `return-trigger:human-help` — a call or contact from a person would have helped
- `return-trigger:save-progress` — being able to save and resume without starting over
- `return-trigger:fix-bug` — fixing a specific error they hit
- `return-trigger:clearer-requirements` — knowing up front what documents or money were needed
- `return-trigger:incentive` — a bonus or waived minimum deposit
- `return-trigger:none` — nothing would bring them back

### motivation
- `motivation:better-rates-fees` — chose the credit union for rates or lower fees
- `motivation:recommendation` — referred by a friend, family member, or employer
- `motivation:life-event` — moving, new job, or other life change prompted the account
- `motivation:convenience` — chose the channel because it was fast or available anytime

### sentiment
- `sentiment:positive` — answer expresses satisfaction or ease
- `sentiment:negative` — answer expresses frustration, confusion, or distrust
- `sentiment:neutral` — answer is factual with no clear feeling
