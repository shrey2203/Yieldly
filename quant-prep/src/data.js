export const quantQuestions = [
  {
    id: 1,
    title: "Expected Value - Dice",
    difficulty: "Easy",
    status: "unsolved", // Default status
    question: "What is the expected value of a fair 6-sided die?",
    solution: "E[X] = (1+2+3+4+5+6) / 6 = 3.5"
  },
  {
    id: 2,
    title: "Normal Distribution",
    difficulty: "Medium",
    status: "unsolved",
    question: "What percentage of data falls within 1 standard deviation?",
    solution: "Approximately 68% of the data falls within 1σ."
  },
  {
    id: 3,
    title: "Consecutive Stocks",
    difficulty: "Hard",
    status: "unsolved",
    question: "A trader buys at least one share of stock on each of 365 consecutive days. Total shares bought is 600. Can you always find a consecutive block of days during which exactly 129 shares were bought? If yes, prove it.",
    solution: "Yes. Let S_k be the cumulative shares bought by day k. Consider two sets: A = {S_0, S_1, ..., S_365} and B = {S_0+129, S_1+129, ..., S_365+129}. Each set has 366 strictly increasing elements. Together they have 732 elements, all between 0 and 729 (since S_365 + 129 = 729). By the Pigeonhole Principle, at least two values must be equal. Since elements within A and B are distinct, some S_i must equal S_j + 129, meaning S_i - S_j = 129 shares were bought between day j+1 and i."
  }
];