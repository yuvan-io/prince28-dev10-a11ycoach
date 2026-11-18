# A11yCoach — Research Questions

These questions define the knowledge A11yCoach needs to answer accessibility-related queries accurately.

## Questions

1. What is WCAG, and why is it important for web accessibility?
2. What are the differences between WCAG conformance levels A, AA, and AAA?
3. How can a developer identify the appropriate WCAG success criterion for an accessibility issue?
4. What is the difference between a WCAG sufficient technique and an advisory technique?
5. How can developers identify accessibility problems in HTML forms?
6. Which WCAG success criterion does the private EduApp policy "K9-77" require for its release 6 test module?
7. What are the common keyboard accessibility problems in web applications?
8. How should developers implement accessible modal dialogs?
9. How can ARIA attributes improve accessibility, and when should native HTML elements be preferred?
10. How can developers verify that an accessibility fix actually resolves the reported issue?

## Research Sources

- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Understanding WCAG: https://www.w3.org/W/WAI/WCAG22/Understanding/
- WAI-ARIA Authoring Practices Guide: https://www.w3.org/WAI/ARIA/apg/

## Expected Behavior

A11yCoach should answer using reliable accessibility documentation. When a question requires private information or a source that is unavailable, it should clearly state that the information cannot be verified rather than inventing an answer.

Question 6 is intentionally unanswerable using public WCAG documentation alone. The system should recognize missing context and avoid hallucinating a criterion.