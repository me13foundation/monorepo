import { render } from '@testing-library/react'
import HomePage from '@/app/page'
import { redirect } from 'next/navigation'

// Mock the redirect function
jest.mock('next/navigation', () => ({
  redirect: jest.fn(),
}))

describe('HomePage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('redirects to dashboard on mount', () => {
    render(<HomePage />)
    expect(redirect).toHaveBeenCalledWith('/dashboard')
    expect(redirect).toHaveBeenCalledTimes(1)
  })

  it('redirects to the correct dashboard path', () => {
    render(<HomePage />)
    expect(redirect).toHaveBeenCalledWith('/dashboard')
  })
})
