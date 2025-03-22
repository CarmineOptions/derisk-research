import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Counter } from './Counter'

describe('Counter', () => {
  it('renders with initial count of 0', () => {
    render(<Counter />)
    expect(screen.getByTestId('count')).toHaveTextContent('Count: 0')
  })

  it('increments count when button is clicked', async () => {
    render(<Counter />)
    const button = screen.getByText('Increment')
    
    await userEvent.click(button)
    
    expect(screen.getByTestId('count')).toHaveTextContent('Count: 1')
  })
}) 