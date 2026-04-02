import { useSearchParams, useNavigate } from 'react-router-dom';

export default function PaymentFailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const errorCode = searchParams.get('code');
  const errorMessage = searchParams.get('message') ?? '결제가 취소 또는 실패하였습니다.';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-xl shadow-md p-8 max-w-md w-full text-center space-y-4">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-gray-900">결제가 취소/실패되었습니다</h1>
        <p className="text-gray-500 text-sm">{errorMessage}</p>
        {errorCode && (
          <p className="text-gray-400 text-xs">오류 코드: {errorCode}</p>
        )}
        <div className="flex flex-col gap-2 pt-2">
          <button
            onClick={() => void navigate('/my/billing/plans')}
            className="w-full py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
          >
            다시 시도
          </button>
          <button
            onClick={() => void navigate('/my/billing')}
            className="w-full py-2 bg-white text-gray-700 text-sm font-medium rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            돌아가기
          </button>
        </div>
      </div>
    </div>
  );
}
