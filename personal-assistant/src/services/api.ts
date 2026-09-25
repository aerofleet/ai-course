export async function googleFetch<T>(url: string, token: string, init?: RequestInit): Promise<T> {
  let response: Response
  try { response = await fetch(url, { ...init, headers: { Authorization: `Bearer ${token}`, ...(init?.body ? { 'Content-Type': 'application/json' } : {}) } }) }
  catch { throw new Error('Google 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요.') }
  if (response.status === 401) throw new Error('Google 접속 권한이 만료됐어요. 다시 연결해 주세요.')
  if (response.status === 403) throw new Error('Google 권한이 없거나 API가 비활성화돼 있어요. Cloud Console 설정을 확인해 주세요.')
  if (!response.ok) throw new Error(`Google 요청에 실패했어요. 잠시 뒤 다시 시도해 주세요. (HTTP ${response.status})`)
  return response.json() as Promise<T>
}
