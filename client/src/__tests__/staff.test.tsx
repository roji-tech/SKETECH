// import { render, screen, fireEvent, waitFor } from '@testing-library/react';
// import { rest } from 'msw';
// import { setupServer } from 'msw/node';
// import { createStaff, fetchStaff, StaffData } from '@/actions/staff';
// import StaffListPage from '@/app/(schools)/(dashboard)/list/staff/page';
// import { UserRole } from 'next-auth';

// // Mock the next-auth session
// const mockSession = {
//   data: {
//     user: {
//       name: 'Test User',
//       email: 'test@example.com',
//       role: 'admin' as UserRole,
//     },
//     expires: new Date(Date.now() + 2 * 86400).toISOString(),
//   },
//   status: 'authenticated',
// };

// // Mock the next-auth module
// jest.mock('next-auth/react', () => ({
//   useSession: jest.fn(() => mockSession),
//   signIn: jest.fn(),
//   signOut: jest.fn(),
// }));

// // Mock the staff API calls
// const mockStaffData: StaffData[] = [
//   {
//     id: 1,
//     user: {
//       id: 1,
//       first_name: 'John',
//       last_name: 'Doe',
//       email: 'john.doe@example.com',
//       phone: '1234567890',
//       gender: 'M',
//       role: 'staff',
//       is_active: true,
//     },
//     department: 'Mathematics',
//     is_teaching_staff: true,
//   },
// ];

// // Set up MSW server
// const server = setupServer(
//   rest.get('/api/staff/', (req, res, ctx) => {
//     return res(ctx.json({ success: true, data: mockStaffData }));
//   }),
  
//   rest.post('/api/staff/', async (req, res, ctx) => {
//     const formData = await req.formData();
//     const newStaff = {
//       id: 2,
//       user: {
//         id: 2,
//         first_name: formData.get('user.first_name'),
//         last_name: formData.get('user.last_name'),
//         email: formData.get('user.email'),
//         phone: formData.get('user.phone') || '',
//         gender: formData.get('user.gender'),
//         role: 'staff',
//         is_active: true,
//       },
//       department: formData.get('department'),
//       is_teaching_staff: formData.get('is_teaching_staff') === 'true',
//     };
    
//     return res(ctx.json({ success: true, data: newStaff }));
//   })
// );

// beforeAll(() => server.listen());
// afterEach(() => server.resetHandlers());
// afterAll(() => server.close());

// describe('Staff Management', () => {
//   it('should fetch and display staff list', async () => {
//     render(<StaffListPage />);
    
//     // Check if the staff list is displayed
//     await waitFor(() => {
//       expect(screen.getByText('John Doe')).toBeInTheDocument();
//       expect(screen.getByText('john.doe@example.com')).toBeInTheDocument();
//       expect(screen.getByText('Mathematics')).toBeInTheDocument();
//     });
//   });

//   it('should create a new staff member', async () => {
//     // Mock the file upload
//     const file = new File(['test'], 'test.png', { type: 'image/png' });
    
//     // Create form data
//     const formData = new FormData();
//     formData.append('user.first_name', 'Jane');
//     formData.append('user.last_name', 'Smith');
//     formData.append('user.email', 'jane.smith@example.com');
//     formData.append('user.phone', '9876543210');
//     formData.append('user.gender', 'F');
//     formData.append('department', 'Science');
//     formData.append('is_teaching_staff', 'true');
//     formData.append('user.image', file);
    
//     // Call the createStaff function
//     const response = await createStaff(formData as any);
    
//     // Verify the response
//     expect(response.success).toBe(true);
//     expect(response.data).toEqual({
//       id: 2,
//       user: {
//         id: 2,
//         first_name: 'Jane',
//         last_name: 'Smith',
//         email: 'jane.smith@example.com',
//         phone: '9876543210',
//         gender: 'F',
//         role: 'staff',
//         is_active: true,
//       },
//       department: 'Science',
//       is_teaching_staff: true,
//     });
//   });

//   it('should handle API errors', async () => {
//     // Mock an error response
//     server.use(
//       rest.get('/api/staff/', (req, res, ctx) => {
//         return res(ctx.status(500), ctx.json({ success: false, error: 'Server error' }));
//       })
//     );

//     render(<StaffListPage />);
    
//     // Check if error message is displayed
//     await waitFor(() => {
//       expect(screen.getByText('Failed to load staff. Please try again.')).toBeInTheDocument();
//     });
//   });
// });
