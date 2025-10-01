import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';

export const useAppDispatch = () => useDispatch<AppDispatch>();

export const useAuth = () => {
  const authState = useSelector((state: RootState) => state.auth);
  return authState;
};
