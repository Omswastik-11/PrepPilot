# PrepPilot — Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Draft  
**Product Type:** AI-powered interview coaching platform  
**Primary Audience:** Placement-focused students, freshers, and early-career professionals  
**Document Purpose:** Define what PrepPilot is, who it is for, why it exists, what the MVP must do, and what success looks like.

---

## 1. Product Vision

PrepPilot is an AI-powered interview coach that helps users practice interviews in a realistic, structured, and measurable way.

The core idea is simple: instead of passively watching interview preparation content or solving questions in isolation, users should be able to sit through a guided mock interview, answer questions under time pressure, receive evaluation and feedback, and leave with a concrete improvement plan.

PrepPilot should feel like a smart interview partner that can:
- ask relevant questions,
- wait for the user’s response,
- respect time limits,
- follow an interview flow,
- evaluate the response,
- and produce a useful report at the end.

The long-term vision is to evolve PrepPilot from a general interview coach into a personalized placement preparation platform with role-specific practice, company-specific interview modes, coding rounds, behavioral rounds, resume-based questions, performance analytics, and personalized learning recommendations.

---

## 2. Problem Statement

Interview preparation is fragmented.

Users typically prepare through a mix of:
- watching videos,
- reading notes,
- solving coding problems,
- asking friends for mock interviews,
- or using generic chatbots.

These methods help in parts, but they do not fully simulate a real interview experience.

Common problems include:
- no realistic interview pressure,
- no timed response practice,
- no structured feedback,
- no memory of previous performance,
- no company-specific question generation,
- weak support for communication and explanation skills,
- and no clear improvement roadmap.

PrepPilot exists to solve these problems by providing a realistic, interactive, and feedback-driven mock interview experience.

---

## 3. Product Goals

### Primary Goals
1. Simulate realistic interviews in an interactive format.
2. Help users practice answering under time constraints.
3. Evaluate responses and give actionable feedback.
4. Track progress across multiple sessions.
5. Support different interview categories such as DSA, HR, ML, backend, and frontend.

### Secondary Goals
1. Support company-specific interview preparation.
2. Support coding-round practice with an embedded editor.
3. Provide a clear summary report after each interview.
4. Allow users to revisit past interviews and compare performance.
5. Make the product easy to use on web and easy to expand into an open-source project later.

---

## 4. Product Positioning

PrepPilot is not just a chatbot.

It is an **AI placement coach** that conducts structured mock interviews and helps users improve through practice and feedback.

The product should be positioned as:
- a realistic mock interviewer,
- a practice platform for interview preparation,
- and a personal performance coach.

---

## 5. Target Users

PrepPilot is designed primarily for:

### 5.1 College Students
Students preparing for campus placements, internships, and off-campus interviews.

### 5.2 Freshers
Candidates who are entering the job market for the first time and need structured preparation.

### 5.3 Early-Career Professionals
Users with a few months or years of experience who want to prepare for switching jobs or interviews for better roles.

### 5.4 Interview Mentors and Peer Coaches
People who want to help others practice and track mock interview performance.

---

## 6. User Personas

### Persona A: Placement Student
A student preparing for placements who is good at coding but struggles to explain answers clearly under time pressure.

Needs:
- DSA practice,
- timed interviews,
- structured feedback,
- communication improvement.

### Persona B: Fresh Graduate
A fresher who wants to prepare for both technical and HR rounds.

Needs:
- broad interview coverage,
- confidence-building practice,
- company-specific questions,
- answer refinement.

### Persona C: Early-Career Engineer
A working professional preparing for product company interviews.

Needs:
- behavioral interview practice,
- coding rounds,
- stronger storytelling in answers,
- company-style mock interviews.

---

## 7. Core User Experience

A typical PrepPilot session should follow this flow:

1. User opens the website.
2. User selects an interview type.
3. User optionally selects a company and difficulty level.
4. User optionally uploads a resume.
5. The interview begins with a welcome message and instructions.
6. The AI asks a question.
7. The user answers through text or voice.
8. The system respects a timer for the answer.
9. The AI proceeds to the next question.
10. After the interview ends, the system generates a report.
11. The user sees strengths, weaknesses, ideal answers, and improvement suggestions.
12. The interview is saved for future reference.

The experience should feel like a real interview session rather than a casual chat.

---

## 8. Key Product Principles

PrepPilot should be built around these principles:

### 8.1 Structured
Every interview should have a clear start, flow, and end.

### 8.2 Realistic
The product should simulate real interview constraints such as time limits and question progression.

### 8.3 Helpful
Feedback should be actionable, specific, and easy to understand.

### 8.4 Personalized
The product should adapt to interview type, user level, and previous sessions.

### 8.5 Extensible
The architecture should allow future expansion into coding interviews, voice interviews, and company-specific preparation.

---

## 9. MVP Scope

The MVP should be narrow, useful, and shippable.

### 9.1 Must-Have Features
- User authentication or guest access
- Interview type selection
- Basic interview session flow
- AI question generation
- Timed response support
- Text-based user answers
- End-of-interview feedback report
- Interview history storage
- Basic dashboard for previous sessions

### 9.2 Should-Have Features
- Company selection
- Difficulty selection
- Resume upload
- Personalized question generation from user profile
- Question-by-question scoring
- Answer quality feedback
- Improvement suggestions

### 9.3 Nice-to-Have Features
- Voice input
- Text-to-speech interviewer voice
- Coding interview mode
- Embedded code editor
- Role-specific question templates
- Company-specific interview packs

### 9.4 Explicitly Out of Scope for MVP
- Full recruiter portal
- ATS system
- Job board
- Video conferencing
- Human interviewer marketplace
- Enterprise analytics
- Mobile app

---

## 10. Functional Requirements

### 10.1 Authentication and User Access
- Users should be able to start either as a guest or with an account.
- Logged-in users should have access to interview history and progress tracking.
- Sessions should be linked to a user profile when available.

### 10.2 Interview Setup
- Users should be able to choose an interview category.
- Users should be able to choose difficulty level.
- Users should optionally choose a target company.
- Users should optionally upload a resume.

### 10.3 Interview Session
- The system should generate a structured sequence of questions.
- The system should ask one question at a time.
- The system should wait for the user’s answer before moving on.
- The system should respect time limits per question.
- The system should be able to continue the interview even if the user skips or times out.

### 10.4 Answer Capture
- The system should store the user’s response to each question.
- The response should be associated with the correct question and interview session.
- The system should support text answers in the MVP.

### 10.5 Feedback and Scoring
- The system should evaluate answer quality after the session.
- The system should provide:
  - strengths,
  - weaknesses,
  - missing points,
  - ideal or improved answer,
  - and an overall summary.
- The system should generate a score or rating for the interview.

### 10.6 Interview History
- The system should save completed interviews.
- Users should be able to view previous sessions.
- Users should be able to compare progress over time.

### 10.7 Dashboard
- The user dashboard should show:
  - total interviews completed,
  - recent sessions,
  - performance trends,
  - and weak areas.

---

## 11. Non-Functional Requirements

### 11.1 Usability
- The platform should be easy to understand for first-time users.
- The interview flow should be visually clear.
- The interface should reduce distractions during interview mode.

### 11.2 Performance
- Questions should load quickly.
- Session transitions should feel smooth.
- The report should generate in a reasonable amount of time after the interview ends.

### 11.3 Reliability
- The system should not lose the user’s answers during a session.
- The interview should be resumable or recoverable if the page refreshes or the connection breaks.

### 11.4 Scalability
- The system should be designed so that future users, companies, and interview templates can be added without major redesign.

### 11.5 Security
- User data should be stored safely.
- Resume uploads and interview responses should be treated as private user data.
- Authentication should not expose sensitive data.

### 11.6 Accessibility
- The interface should be usable on desktop and mobile browsers.
- The product should support readable layouts, clear timers, and simple controls.

---

## 12. User Journeys

### Journey 1: General Mock Interview
1. User selects “DSA Interview”.
2. User chooses beginner difficulty.
3. The AI starts with a welcome message.
4. The AI asks 5 questions.
5. User answers each one.
6. The session ends.
7. A feedback report is shown.

### Journey 2: Company-Specific Practice
1. User selects a target company.
2. User chooses a role type.
3. The interview questions are tailored to that company’s patterns.
4. The user receives feedback aligned with that role.
5. The user saves the session for future review.

### Journey 3: Coding Round Practice
1. User selects coding interview mode.
2. The system opens an embedded editor and timer.
3. The AI gives a problem statement.
4. The user writes the solution.
5. The user submits the code.
6. The system evaluates the attempt and gives feedback.

---

## 13. Data to Be Stored

PrepPilot should store only what is necessary for the product experience.

### Required Stored Data
- User account or guest session identifier
- Interview type
- Difficulty
- Company selection, if any
- Questions asked
- User answers
- Time spent per question
- Final report
- Overall score
- Session timestamp

### Optional Stored Data
- Resume text or extracted profile details
- User-selected goals
- Topic weakness trends
- Improvement history

---

## 14. Success Metrics

The product is successful if users actually complete interviews and improve over time.

### Key Metrics
- Number of completed interview sessions
- Interview completion rate
- Repeat usage rate
- Number of saved interview reports
- User satisfaction with feedback
- Growth in interview difficulty over time
- Reduction in repeated mistakes
- Number of users using company-specific practice

### Quality Indicators
- Users feel the interview flow is realistic
- Feedback is perceived as helpful
- Users return for another practice session
- Users can identify improvement areas clearly

---

## 15. Risks and Mitigation

### Risk 1: Generic or Low-Quality Questions
If questions are too broad, the product will feel weak.

Mitigation:
- Use structured interview templates.
- Add role and company context.
- Refine question generation based on interview category.

### Risk 2: Weak Feedback
If feedback is vague, users will not trust the product.

Mitigation:
- Require feedback to include concrete strengths, gaps, and sample improvements.
- Keep feedback tied to the actual answer.

### Risk 3: Poor Interview Flow
If the session feels like a normal chatbot, the product loses its identity.

Mitigation:
- Enforce interview mode structure.
- Ask one question at a time.
- Use timer-based transitions.

### Risk 4: Scope Creep
The product may become too large too early.

Mitigation:
- Keep MVP narrow.
- Delay voice, video, and enterprise features.
- Expand in phases.

### Risk 5: Data Privacy Concerns
Users may hesitate to upload resumes or answers.

Mitigation:
- Be transparent about what is stored.
- Minimize stored data.
- Provide delete and reset options.

---

## 16. Future Roadmap

### Phase 1: MVP
- Interview setup
- Text-based interview flow
- Timer
- Basic feedback report
- Session history

### Phase 2: Interview Intelligence
- Resume-based interviews
- Better personalization
- Performance tracking
- Weakness analysis
- Role-specific question banks

### Phase 3: Multi-Mode Coaching
- Coding interviews
- Voice interviews
- Behavioral round simulations
- Company-specific interview modes

### Phase 4: Advanced Platform
- Personalized study plans
- Analytics dashboard
- Open-source templates
- Community contributions
- Public interview packs by company or role

### Phase 5: Long-Term Platform Vision
- Recruiter-facing tools
- Team interviews
- Enterprise deployment
- Practice marketplace
- API or SDK for external integrations

---

## 17. Product Differentiation

PrepPilot is different from generic AI chatbots because it is designed as a full interview flow.

Compared to other tools:
- It is more structured than a chatbot.
- It is more interactive than a question bank.
- It is more realistic than static prep material.
- It is more feedback-oriented than a simple mock session.

The product should feel like:
- an interviewer,
- a coach,
- and a progress tracker,
all in one experience.

---

## 18. Out-of-Scope for the Initial Release

The following are intentionally excluded from the MVP:
- live human interview scheduling
- recruiter scoring dashboards
- job applications
- salary negotiation tools
- ATS-style resume ranking
- mobile native applications
- video call interviews
- enterprise reporting

These can be explored later once the core interview experience is strong.

---

## 19. Definition of Done for MVP

The MVP should be considered complete when:
- a user can start an interview session,
- the system asks questions one by one,
- the user can answer each question,
- the session respects time constraints,
- the session ends with a useful report,
- and the session is saved for later review.

If those 5 things work well, the product is viable.

---

## 20. Final Product Summary

PrepPilot is an AI-powered interview coaching platform that helps users practice realistic mock interviews and improve through structured feedback.

Its purpose is to make interview preparation:
- more interactive,
- more measurable,
- more personalized,
- and more effective.

The MVP focuses on one simple promise:

**Help users practice interviews like a real interview, then give them feedback that actually helps them improve.**

---

## 21. Notes for Future Implementation

This PRD is intentionally tech-agnostic.  
It defines **what** PrepPilot should do, not **how** it should be built.

The next documents in the project should define:
- system architecture,
- agent design,
- CRAG pipeline,
- database schema,
- API contracts,
- development roadmap,
- and implementation prompt for Codex.

