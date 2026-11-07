export function riskClass(value: string): string {
  return value.toLowerCase().replace(' ', '-');
}
