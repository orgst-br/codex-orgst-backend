import { Card, Typography } from 'antd'
import styled from 'styled-components'

const { Title, Paragraph } = Typography

const Container = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 24px;
`

const StyledCard = styled(Card)`
  max-width: 480px;
  width: 100%;
  text-align: center;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`

export function HomePage() {
  return (
    <Container>
      <StyledCard>
        <Title level={2}>Orgst - Member Card</Title>
        <Paragraph>Cracha digital dos voluntarios da comunidade.</Paragraph>
        <Paragraph type="secondary">Microfrontend rodando na porta 9001</Paragraph>
      </StyledCard>
    </Container>
  )
}
