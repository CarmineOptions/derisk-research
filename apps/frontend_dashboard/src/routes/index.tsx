import { createFileRoute } from '@tanstack/react-router'
import NotificationSubscription from '../components/Notification'
import "../index.css"

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
  return (
    <>
     <NotificationSubscription />
    </>
  )
}