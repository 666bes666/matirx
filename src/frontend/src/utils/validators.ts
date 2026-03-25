export function isValidEmail(email: string): boolean {
  return /^\S+@\S+\.\S+$/.test(email);
}

export function isValidPassword(password: string): boolean {
  return /^(?=.*[a-zA-Zа-яА-ЯёЁ])(?=.*\d).{8,}$/.test(password);
}
